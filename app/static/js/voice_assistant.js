/**
 * MindGuard - AI Voice Assistant Engine
 * Handles SpeechRecognition, SpeechSynthesis, Web Audio Visualizations, and State Management.
 */

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const micBtn = document.getElementById('mic-toggle-btn');
    const micIcon = document.getElementById('mic-icon');
    const avatar = document.getElementById('ai-avatar');
    const statusText = document.getElementById('status-text');
    const statusDot = document.getElementById('status-dot');
    const transcriptContainer = document.getElementById('transcript-container');
    const audioCanvas = document.getElementById('audio-canvas');
    const canvasCtx = audioCanvas.getContext('2d');
    const placeholderText = document.getElementById('placeholder-text');

    // State
    let isListening = false;
    let isMuted = true;
    let currentState = 'idle'; // idle, listening, processing, speaking
    let recognition = null;
    let synth = window.speechSynthesis;
    let audioContext = null;
    let analyser = null;
    let microphoneStream = null;
    let dataArray = null;
    let timeDomainArray = null;
    let animationId = null;

    // Acoustic Feature Tracking (Reset per utterance)
    let acousticData = {
        pitchAccumulator: 0,
        pitchCount: 0,
        rmsAccumulator: 0,
        rmsCount: 0,
        frameCount: 0
    };

    // Initialize Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false; // Stop after a pause
        recognition.interimResults = true; // Show live text typing
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isListening = true;

            // Reset acoustic metrics for this utterance
            acousticData = {
                pitchAccumulator: 0,
                pitchCount: 0,
                rmsAccumulator: 0,
                rmsCount: 0,
                frameCount: 0
            };

            updateState('listening');
            updateMicUI(true);
        };

        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            if (interimTranscript) {
                updateLiveTranscript(interimTranscript, true);
            }

            if (finalTranscript) {
                updateLiveTranscript(finalTranscript, false, 'user');
                processUserMessage(finalTranscript);
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            if (event.error !== 'no-speech') {
                updateState('idle');
                updateMicUI(false);
            }
        };

        recognition.onend = () => {
            // If we are just idle and mic is still toggled "on", restart it
            if (!isMuted && currentState === 'listening') {
                // The user stopped talking, but we haven't hit processing yet
                // Optional: auto-restart listening if desired, but typical behavior
                // is to wait for them to click again or process the last sentence.
            }
        };
    } else {
        alert("Your browser does not support the Web Speech API. Please use Google Chrome or Edge.");
    }

    // Toggle Microphone
    micBtn.addEventListener('click', async () => {
        if (isMuted) {
            // Turn ON
            try {
                await setupAudioVisualization();
                isMuted = false;
                startListening();
            } catch (err) {
                console.error("Mic access denied or failed", err);
                alert("Please allow microphone access to use the Voice Assistant.");
            }
        } else {
            // Turn OFF
            isMuted = true;
            stopListening();
            updateState('idle');
            updateMicUI(false);
        }
    });

    function startListening() {
        if (recognition && !isListening && currentState !== 'processing' && currentState !== 'speaking') {
            if (placeholderText) placeholderText.style.display = 'none';
            recognition.start();
        }
    }

    function stopListening() {
        if (recognition && isListening) {
            recognition.stop();
            isListening = false;
        }
    }

    function updateMicUI(active) {
        if (active) {
            micIcon.classList.remove('bi-mic-fill');
            micIcon.classList.add('bi-mic-mute-fill', 'text-rose-500');
            micBtn.classList.remove('bg-white');
            micBtn.classList.add('bg-rose-50');
        } else {
            micIcon.classList.remove('bi-mic-mute-fill', 'text-rose-500');
            micIcon.classList.add('bi-mic-fill');
            micBtn.classList.remove('bg-rose-50');
            micBtn.classList.add('bg-white');
        }
    }

    // Audio Visualization Setup
    async function setupAudioVisualization() {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            microphoneStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });

            const source = audioContext.createMediaStreamSource(microphoneStream);
            analyser = audioContext.createAnalyser();

            // Configuration for smooth circular waves
            analyser.fftSize = 256;
            analyser.smoothingTimeConstant = 0.8;

            source.connect(analyser);

            const bufferLength = analyser.frequencyBinCount;
            dataArray = new Uint8Array(bufferLength);
            timeDomainArray = new Float32Array(analyser.fftSize);

            drawWaveform();
        }
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }
    }

    function drawWaveform() {
        animationId = requestAnimationFrame(drawWaveform);

        if (!analyser) return;
        analyser.getByteFrequencyData(dataArray);
        analyser.getFloatTimeDomainData(timeDomainArray);

        canvasCtx.clearRect(0, 0, audioCanvas.width, audioCanvas.height);

        // Acoustic Processing Loop (Only when listening to user)
        if (currentState === 'listening') {
            acousticData.frameCount++;

            // 1. Calculate RMS Energy
            let rmsSqSum = 0;
            for (let i = 0; i < timeDomainArray.length; i++) {
                rmsSqSum += timeDomainArray[i] * timeDomainArray[i];
            }
            let rms = Math.sqrt(rmsSqSum / timeDomainArray.length);
            // Ignore silence when accumulating averge energy
            if (rms > 0.01) {
                acousticData.rmsAccumulator += rms;
                acousticData.rmsCount++;

                // 2. Simple Zero-Crossing Rate (ZCR) for proxying Pitch/Frequency variations
                let zeroCrossings = 0;
                for (let i = 1; i < timeDomainArray.length; i++) {
                    if (timeDomainArray[i - 1] > 0 && timeDomainArray[i] <= 0) {
                        zeroCrossings++;
                    }
                }
                let zcrFreq = (zeroCrossings * audioContext.sampleRate) / (2 * analyser.fftSize);
                if (zcrFreq > 50 && zcrFreq < 500) { // Bound to human voice ranges (rough)
                    acousticData.pitchAccumulator += zcrFreq;
                    acousticData.pitchCount++;
                }
            }
        }

        // Only draw strongly if listening or speaking
        if (currentState !== 'listening' && currentState !== 'speaking') return;

        const centerX = audioCanvas.width / 2;
        const centerY = audioCanvas.height / 2;
        const radius = 65; // Just outside the core

        canvasCtx.beginPath();
        const bars = parseInt(dataArray.length / 1.5); // Use lower frequencies mostly
        const angleStep = (Math.PI * 2) / bars;

        for (let i = 0; i < bars; i++) {
            const amplitude = dataArray[i]; // 0 to 255
            const waveScale = currentState === 'speaking' ? 0.3 : 0.15; // AI speaks bigger waves
            const dynamicRadius = radius + (amplitude * waveScale);

            const angle = i * angleStep;
            const x = centerX + Math.cos(angle) * dynamicRadius;
            const y = centerY + Math.sin(angle) * dynamicRadius;

            if (i === 0) {
                canvasCtx.moveTo(x, y);
            } else {
                canvasCtx.lineTo(x, y);
            }
        }

        canvasCtx.closePath();

        // Style the waveform based on who is talking
        if (currentState === 'speaking') {
            canvasCtx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
            canvasCtx.lineWidth = 4;
            canvasCtx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        } else {
            // Listening (User talking)
            canvasCtx.strokeStyle = 'rgba(56, 189, 248, 0.6)';
            canvasCtx.lineWidth = 3;
            canvasCtx.fillStyle = 'transparent';
        }

        canvasCtx.fill();
        canvasCtx.stroke();
    }

    // State & Emotion Management
    function updateState(newState) {
        // Remove old state
        avatar.classList.remove(`state-${currentState}`);
        currentState = newState;
        // Add new state
        avatar.classList.add(`state-${currentState}`);

        // Update top bar UI
        switch (newState) {
            case 'idle':
                statusText.textContent = 'STANDBY';
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-slate-400';
                break;
            case 'listening':
                statusText.textContent = 'LISTENING...';
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-blue-400 animate-pulse';
                break;
            case 'processing':
                statusText.textContent = 'ANALYZING';
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-pink-400 animate-pulse';
                break;
            case 'speaking':
                statusText.textContent = 'RESPONDING';
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-white animate-pulse';
                break;
        }
    }

    function updateEmotion(categoryName) {
        // Find existing emotion class and remove it
        avatar.className = avatar.className.replace(/\bemotion-\S+/g, '');

        // Map backend category strings to our CSS themes
        const lowerCat = (categoryName || '').toLowerCase();
        let newEmotionClass = 'emotion-healthy'; // default

        if (lowerCat.includes('stress') || lowerCat.includes('anxiety') || lowerCat.includes('moderate')) {
            newEmotionClass = 'emotion-moderate';
        } else if (lowerCat.includes('depress') || lowerCat.includes('high') || lowerCat.includes('red')) {
            newEmotionClass = 'emotion-high';
        }

        avatar.classList.add(newEmotionClass);
    }

    // Handle Transcript UI
    let currentInterimElement = null;

    function updateLiveTranscript(text, isInterim, sender = 'user') {
        if (placeholderText) placeholderText.style.display = 'none';

        if (isInterim) {
            if (!currentInterimElement) {
                currentInterimElement = document.createElement('p');
                currentInterimElement.className = 'text-white/60 text-lg font-light italic leading-relaxed';
                transcriptContainer.appendChild(currentInterimElement);
            }
            currentInterimElement.textContent = text;
        } else {
            // Final text
            if (currentInterimElement) {
                currentInterimElement.remove();
                currentInterimElement = null;
            }

            const p = document.createElement('p');
            if (sender === 'user') {
                p.className = 'text-white/90 text-xl font-medium leading-relaxed';
                p.innerHTML = `<span class="text-blue-400 text-sm font-bold tracking-widest uppercase mr-3">You</span> ${text}`;
            } else {
                p.className = 'text-slate-300 text-lg font-light leading-relaxed';
                p.innerHTML = `<span class="text-pink-400 text-sm font-bold tracking-widest uppercase mr-3">AI</span> ${text}`;

                // Add action buttons dynamically if the AI suggested a test
                if (text.toLowerCase().includes('quick mood check') || text.toLowerCase().includes('color test')) {
                    const btnHtml = `<div class="mt-3 flex gap-2">
                        <a href="/tests/color-test" class="px-4 py-2 bg-gradient-to-r from-calm-500 to-lav-500 text-white rounded-lg text-sm font-semibold shadow hover:scale-105 transition-transform">Start Color Test</a>
                        <a href="/tests/image-test/start" class="px-4 py-2 bg-slate-800 border border-slate-700 text-white rounded-lg text-sm font-semibold hover:bg-slate-700 transition">Start Image Test</a>
                    </div>`;
                    p.innerHTML += btnHtml;
                }
            }

            transcriptContainer.appendChild(p);
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
        }
    }

    // Backend Communication
    async function processUserMessage(message) {
        stopListening();
        updateState('processing');

        try {
            // Compute final acoustic aggregates to send
            let avgPitch = acousticData.pitchCount > 0 ? (acousticData.pitchAccumulator / acousticData.pitchCount) : 0;
            let avgEnergy = acousticData.rmsCount > 0 ? (acousticData.rmsAccumulator / acousticData.rmsCount) : 0;
            // Frame count relates to duration, rmsCount relates to active speech time
            let speechSpeed = acousticData.frameCount > 0 ? (acousticData.rmsCount / acousticData.frameCount) : 0;

            const payload = {
                message: message,
                acoustic_features: {
                    pitch: avgPitch,
                    energy: avgEnergy,
                    speech_speed: speechSpeed
                }
            };

            const response = await fetch('/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            if (data.ai_response) {
                updateLiveTranscript(data.ai_response, false, 'ai');
                updateEmotion(data.risk_level === 'RED' ? 'High Risk' : (data.risk_level === 'AMBER' ? 'Moderate' : 'Healthy'));
                speakResponse(data.ai_response);
            }
        } catch (error) {
            console.error('Error fetching AI response:', error);
            updateLiveTranscript('I experienced a connection issue. Please try speaking again.', false, 'ai');
            updateState('idle');
            if (!isMuted) setTimeout(startListening, 1000);
        }
    }

    // Text to Speech
    function speakResponse(text) {
        if (!synth) {
            updateState('idle');
            if (!isMuted) startListening();
            return;
        }

        // Cancel any ongoing speech
        synth.cancel();
        // Strip markdown asterisks and URLs for cleaner reading
        const cleanText = text.replace(/\*/g, '').replace(/https?:\/\/[^\s]+/g, 'a link');
        const utterance = new SpeechSynthesisUtterance(cleanText);

        // Find appropriate voice based on language toggle
        const voices = synth.getVoices();

        // Enforce English voice
        utterance.lang = 'en-US';
        const preferredVoice = voices.find(v => v.name.includes('Google UK English Female') || v.name.includes('Microsoft Zira') || v.name.includes('Samantha') || v.name.includes('Natural'))
            || voices.find(v => v.name.includes('Female'))
            || voices.find(v => v.name.includes('Google'))
            || voices[0];
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        // Slower rate and slightly lower pitch creates a much smoother, calming tone
        utterance.rate = 0.95;
        utterance.pitch = 0.9;

        utterance.onstart = () => {
            updateState('speaking');
        };

        utterance.onend = () => {
            updateState('idle');
            if (!isMuted) {
                // Short delay before listening again to avoid echoing itself
                setTimeout(startListening, 500);
            }
        };

        utterance.onerror = (e) => {
            console.error('TTS Error:', e);
            updateState('idle');
            if (!isMuted) startListening();
        };

        synth.speak(utterance);
    }

    // Ensure voices are loaded (Chrome loads them async)
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = () => synth.getVoices();
    }
});

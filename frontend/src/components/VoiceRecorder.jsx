import React, { useState, useRef } from 'react';
import { voiceAPI, formsAPI } from '../services/api';
import './VoiceRecorder.css';

function VoiceRecorder({ onFormCreated }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');
  const [language, setLanguage] = useState('en');
  const [formType, setFormType] = useState('kyc');
  // Separate loading states — transcribing, processing, and TTS are independent actions
  const [transcribing, setTranscribing] = useState(false);
  const [processingForm, setProcessingForm] = useState(false);
  const [generatingSpeech, setGeneratingSpeech] = useState(false);
  const [error, setError] = useState('');
  const [audioUrl, setAudioUrl] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null); // Track stream separately so we can always close it

  const isLoading = transcribing || processingForm || generatingSpeech;

  const checkBrowserSupport = () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError(
        'Your browser does not support microphone recording. ' +
        'Try Chrome or Firefox on a device with a microphone.'
      );
      return false;
    }
    if (typeof MediaRecorder === 'undefined') {
      setError('MediaRecorder is not supported in this browser.');
      return false;
    }
    return true;
  };

  const startRecording = async () => {
    if (!checkBrowserSupport()) return;

    setError('');
    setAudioUrl('');

    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Microphone access denied. Please allow microphone access in your browser settings.');
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.');
      } else {
        setError(`Could not access microphone: ${err.message}`);
      }
      return;
    }

    audioChunksRef.current = [];
    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      // Always close the stream — in onstop, not after transcription
      // so the microphone indicator disappears immediately on stop
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      transcribeAudio(blob);
    };

    recorder.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    setTranscribing(true);
    setError('');
    try {
      const response = await voiceAPI.transcribe(audioBlob, language);
      setTranscribedText(response.data.text);
    } catch (err) {
      setError(err.response?.data?.detail || 'Transcription failed. Check your audio and try again.');
    } finally {
      setTranscribing(false);
    }
  };

  const handleProcessForm = async () => {
    if (!transcribedText.trim()) {
      setError('No text to process.');
      return;
    }
    setProcessingForm(true);
    setError('');
    try {
      const response = await formsAPI.processVoice(transcribedText, formType);
      onFormCreated(response.data);
      setTranscribedText('');
      setAudioUrl('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Form processing failed.');
    } finally {
      setProcessingForm(false);
    }
  };

  const handleTextToSpeech = async () => {
    if (!transcribedText.trim()) {
      setError('No text to convert to speech.');
      return;
    }
    setGeneratingSpeech(true);
    setError('');
    try {
      const response = await voiceAPI.synthesize(transcribedText, language);
      setAudioUrl(response.data.audio_url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Text-to-speech failed.');
    } finally {
      setGeneratingSpeech(false);
    }
  };

  return (
    <div className="voice-recorder">
      <h2>Voice Input</h2>

      <div className="controls-section">
        <div className="control-group">
          <label htmlFor="language-select">Language</label>
          <select
            id="language-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isRecording}
          >
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="mr">Marathi</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="form-type-select">Form Type</label>
          <select
            id="form-type-select"
            value={formType}
            onChange={(e) => setFormType(e.target.value)}
            disabled={isRecording}
          >
            <option value="kyc">Bank KYC</option>
            <option value="medical">Medical Form</option>
            <option value="government">Government Form</option>
          </select>
        </div>
      </div>

      <div className="recording-section">
        <button
          className={`record-button ${isRecording ? 'recording' : ''}`}
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isLoading && !isRecording}
          aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        >
          {isRecording ? '⏹ Stop Recording' : '🎤 Start Recording'}
        </button>

        {isRecording && (
          <div className="recording-indicator" role="status" aria-live="polite">
            Recording...
          </div>
        )}
        {transcribing && (
          <div className="loading-spinner" role="status">
            Transcribing audio...
          </div>
        )}
      </div>

      {transcribedText && (
        <div className="transcription-section">
          <h3>Transcribed Text</h3>
          <textarea
            value={transcribedText}
            onChange={(e) => setTranscribedText(e.target.value)}
            rows="6"
            placeholder="Transcribed text will appear here. You can edit it before processing."
            aria-label="Transcribed speech text"
          />

          <div className="action-buttons">
            <button
              onClick={handleProcessForm}
              disabled={processingForm || isRecording}
              className="btn-primary"
            >
              {processingForm ? 'Processing...' : 'Process Form'}
            </button>

            <button
              onClick={handleTextToSpeech}
              disabled={generatingSpeech || isRecording}
              className="btn-secondary"
            >
              {generatingSpeech ? 'Generating...' : '🔊 Text to Speech'}
            </button>
          </div>
        </div>
      )}

      {audioUrl && (
        <div className="audio-playback">
          <h4>Audio Playback</h4>
          <audio controls src={audioUrl} aria-label="Text to speech audio" />
        </div>
      )}

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}

export default VoiceRecorder;

const messagesEl = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const connectionLabel = document.querySelector("#connection-label");
const newChatButton = document.querySelector("#new-chat");
const micButton = document.querySelector("#mic-button");
const micLabel = document.querySelector("#mic-label");
const composerHint = document.querySelector("#composer-hint");

let conversationId = localStorage.getItem("maxy_conversation_id");
let mediaRecorder = null;
let mediaStream = null;
let audioChunks = [];
let voiceEnabled = false;
let speakVoiceReply = false;
let recording = false;
let activeAudioUrl = null;

function addMessage(role, content) {
  const welcome = document.querySelector("#welcome");
  if (welcome) welcome.remove();

  const wrapper = document.createElement("article");
  wrapper.className = `message ${role}`;

  const label = document.createElement("span");
  label.className = "message-role";
  label.textContent = role === "user" ? "YOU" : "MAXY";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = content;

  wrapper.append(label, bubble);
  if (role === "assistant" && voiceEnabled) {
    const speakButton = document.createElement("button");
    speakButton.className = "speak-button";
    speakButton.type = "button";
    speakButton.textContent = "▶ Listen";
    speakButton.addEventListener("click", () => speakText(content));
    wrapper.append(speakButton);
  }
  messagesEl.append(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setBusy(busy) {
  sendButton.disabled = busy;
  input.disabled = busy;
  sendButton.innerHTML = busy ? "<span>…</span>" : "<span>↑</span>";
  micButton.disabled = busy || !voiceEnabled || !navigator.mediaDevices;
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("API unavailable");
    const health = await response.json();
    connectionLabel.textContent = `API connected · ${health.model}`;
    connectionLabel.previousElementSibling.classList.add("online");
  } catch {
    connectionLabel.textContent = "Local API unavailable";
    connectionLabel.previousElementSibling.classList.remove("online");
  }
}

async function checkVoice() {
  try {
    const response = await fetch("/api/voice/status");
    const status = await response.json();
    voiceEnabled = response.ok && status.enabled;
    const canRecord = Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
    micButton.disabled = !voiceEnabled || !canRecord;
    if (voiceEnabled && canRecord) {
      micLabel.textContent = "Push to talk";
      composerHint.textContent = "Hold no button: tap Start, speak, then tap Stop. Audio is processed locally.";
    } else if (!voiceEnabled) {
      micLabel.textContent = "Voice disabled";
      composerHint.textContent = "Enable voice in .env with MAXY_VOICE_ENABLED=true, then restart MAXY.";
    } else {
      micLabel.textContent = "Mic unsupported";
      composerHint.textContent = "This browser does not support microphone recording. Text chat remains available.";
    }
  } catch {
    micButton.disabled = true;
    micLabel.textContent = "Voice unavailable";
  }
}

async function loadConversation() {
  if (!conversationId) return;
  try {
    const response = await fetch(`/api/conversations/${encodeURIComponent(conversationId)}/messages`);
    if (!response.ok) {
      conversationId = null;
      localStorage.removeItem("maxy_conversation_id");
      return;
    }
    const history = await response.json();
    if (history.length) {
      const welcome = document.querySelector("#welcome");
      if (welcome) welcome.remove();
      history.forEach((item) => addMessage(item.role, item.content));
    }
  } catch {
    // A failed history fetch should not prevent starting a fresh conversation.
  }
}

async function speakText(text) {
  if (!voiceEnabled) return;
  try {
    const response = await fetch("/api/voice/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Speech generation failed.");
    }
    const audioBlob = await response.blob();
    if (activeAudioUrl) URL.revokeObjectURL(activeAudioUrl);
    activeAudioUrl = URL.createObjectURL(audioBlob);
    const player = new Audio(activeAudioUrl);
    player.addEventListener("ended", () => {
      URL.revokeObjectURL(activeAudioUrl);
      activeAudioUrl = null;
    }, { once: true });
    await player.play();
  } catch (error) {
    addMessage("assistant", `I couldn't speak that response. ${error.message}`);
  }
}

async function sendMessage(message, fromVoice = false) {
  const clean = message.trim();
  if (!clean || sendButton.disabled) return;

  addMessage("user", clean);
  input.value = "";
  input.style.height = "auto";
  setBusy(true);
  speakVoiceReply = fromVoice;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: clean, conversation_id: conversationId }),
    });
    const data = await response.json();
    const returnedConversationId = response.headers.get("X-Conversation-ID");
    if (returnedConversationId) {
      conversationId = returnedConversationId;
      localStorage.setItem("maxy_conversation_id", conversationId);
    }
    if (!response.ok) {
      throw new Error(data.detail || "MAXY could not complete the request.");
    }
    conversationId = data.conversation_id;
    localStorage.setItem("maxy_conversation_id", conversationId);
    addMessage("assistant", data.reply);
    if (speakVoiceReply) await speakText(data.reply);
  } catch (error) {
    addMessage("assistant", `I couldn't complete that request. ${error.message}`);
  } finally {
    speakVoiceReply = false;
    setBusy(false);
    input.focus();
  }
}

async function startRecording() {
  if (!voiceEnabled || recording) return;
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    const preferredType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "";
    mediaRecorder = new MediaRecorder(mediaStream, preferredType ? { mimeType: preferredType } : {});
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size) audioChunks.push(event.data);
    });
    mediaRecorder.addEventListener("stop", processRecording, { once: true });
    mediaRecorder.start();
    recording = true;
    micButton.classList.add("recording");
    micLabel.textContent = "Stop recording";
    composerHint.textContent = "Listening… Tap Stop when you've finished speaking.";
  } catch (error) {
    composerHint.textContent = `Microphone access failed: ${error.message}`;
    releaseMicrophone();
  }
}

function stopRecording() {
  if (!recording || !mediaRecorder) return;
  recording = false;
  micButton.classList.remove("recording");
  micLabel.textContent = "Processing audio…";
  micButton.disabled = true;
  mediaRecorder.stop();
}

function releaseMicrophone() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }
}

async function processRecording() {
  releaseMicrophone();
  try {
    const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
    if (!blob.size) throw new Error("No audio was captured. Please try again.");
    const extension = blob.type.includes("ogg") ? "ogg" : "webm";
    const formData = new FormData();
    formData.append("audio", blob, `maxy-recording.${extension}`);
    const response = await fetch("/api/voice/transcribe", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Transcription failed.");
    input.value = data.text;
    composerHint.textContent = `Heard: “${data.text}” — sending to MAXY…`;
    await sendMessage(data.text, true);
  } catch (error) {
    composerHint.textContent = `Voice input failed: ${error.message}`;
  } finally {
    audioChunks = [];
    mediaRecorder = null;
    micButton.disabled = !voiceEnabled;
    micLabel.textContent = "Push to talk";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
});

micButton.addEventListener("click", () => {
  if (recording) stopRecording();
  else startRecording();
});

newChatButton.addEventListener("click", () => {
  conversationId = null;
  localStorage.removeItem("maxy_conversation_id");
  messagesEl.innerHTML = `
    <div id="welcome" class="welcome">
      <div class="welcome-orb"><span>M</span></div>
      <p class="eyebrow">HELLO, I'M MAXY</p>
      <h2>What can I help you think through?</h2>
      <p class="welcome-copy">Type a message or use push-to-talk. Your speech is processed locally on this computer.</p>
      <div class="suggestions">
        <button type="button" data-prompt="Help me plan my day.">Plan my day</button>
        <button type="button" data-prompt="Explain a difficult topic in simple terms.">Explain something</button>
        <button type="button" data-prompt="Help me break a project into steps.">Organize a project</button>
      </div>
    </div>`;
});

messagesEl.addEventListener("click", (event) => {
  const button = event.target.closest("[data-prompt]");
  if (button) sendMessage(button.dataset.prompt);
});

checkHealth();
checkVoice();
loadConversation();

const socket = io();
const logContainer = document.getElementById("log-messages");
const webcam = document.getElementById("webcam");
let lastActivity = Date.now();

// ---------------- 1. INITIALIZATION SEQUENCE (5s) ----------------
function runInitSequence() {
    const statusItems = [
        { id: "stat-camera", label: "Connected" },
        { id: "stat-mic", label: "Ready" },
        { id: "stat-model", label: "Loaded" },
        { id: "stat-speech", label: "Active" }
    ];

    // Stagger status updates every 1.2 seconds
    statusItems.forEach((item, index) => {
        setTimeout(() => {
            const span = document.querySelector(`#${item.id} span`);
            if (span) {
                span.innerText = item.label;
                span.className = "status-ready";
            }
        }, (index + 1) * 1100); 
    });

    // Switch screens and start camera at 5 seconds
    setTimeout(() => {
        document.getElementById("dashboard-screen").classList.remove("active");
        document.getElementById("session-screen").classList.add("active");
        
        // Auto-start Video Feed
        webcam.src = "/video_feed";
        
        // Mark first activity to start the 60s timer correctly
        lastActivity = Date.now();
    }, 5000);
}

// ---------------- 2. COMMUNICATION & AUTO-SCROLL ----------------
socket.on("new_speech", function(data) {
    if (!data.text) return;

    // Reset inactivity timer
    lastActivity = Date.now();

    const emptyMsg = document.querySelector(".empty-msg");
    if (emptyMsg) emptyMsg.remove();

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    
    // Position bubble based on sender
    if (data.sender === "deaf") {
        bubble.classList.add("bubble-right");
    } else {
        bubble.classList.add("bubble-left");
    }

    bubble.innerText = data.text;
    logContainer.appendChild(bubble);

    // AUTO-SCROLL to bottom
    logContainer.scrollTop = logContainer.scrollHeight;
});

// ---------------- 3. 60-SECOND AUTO-CLEAR ----------------
setInterval(() => {
    const now = Date.now();
    const secondsInactive = (now - lastActivity) / 1000;

    // Only clear if the log isn't already empty
    const hasMessages = logContainer.children.length > 0 && !logContainer.querySelector(".empty-msg");

    if (secondsInactive >= 80 && hasMessages) {
        logContainer.innerHTML = '<div class="empty-msg">No messages yet</div>';
        console.log("Logs cleared after 60s of inactivity.");
    }
}, 1000);

// Initialize on Load
window.onload = runInitSequence;
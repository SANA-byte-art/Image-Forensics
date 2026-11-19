/* =====================================================
   IMAGE PREVIEW FUNCTION
===================================================== */

function previewImage(event) {

    let preview   = document.getElementById("imagePreview");
    let container = document.getElementById("previewContainer");

    let file = event.target.files[0];

    if (file) {

        let reader = new FileReader();

        reader.onload = function(e) {
            preview.src = e.target.result;
            container.style.display = "block";
        };

        reader.readAsDataURL(file);
    }
}


/* =====================================================
   PREDICTION FUNCTION
===================================================== */

function predictImage() {

    let fileInput = document.getElementById("imageInput");

    if (!fileInput.files.length) {
        alert("Please select an image first.");
        return;
    }

    let formData = new FormData();
    formData.append("image", fileInput.files[0]);

    fetch("/predict", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {

        if (data.error) {
            alert(data.error);
            return;
        }

        document.getElementById("resultBox").style.display = "block";

        let statusText    = document.getElementById("analysisStatus");
        let progressBar   = document.getElementById("progressBar");
        let progressValue = document.getElementById("progressValue");

        // Reset UI
        statusText.innerText = "";
        statusText.classList.remove("analysis-visible");

        progressBar.classList.remove(
            "glow-finish-high",
            "glow-finish-medium",
            "glow-finish-low"
        );

        progressValue.textContent = "0%";
        progressBar.style.background =
            "conic-gradient(#2a2a2a 0deg, #2a2a2a 0deg)";

        document.getElementById("predictionLabel").innerText =
            "Prediction: " + data.label;

        
         /* ✅ YOUR EXPLANATION CODE (ADDED HERE — CORRECT PLACE) */ 
         
        let explanation = "";

        if (data.label === "AI-Generated") {
            explanation = "This image shows patterns typical of AI-generated content such as unnatural textures and inconsistencies.";
        }

        else if (data.label === "Manipulated") {
             explanation = "This image may have been altered. Signs of editing or tampering are detected.";
        }
        
        else {
            explanation = "This image appears authentic with no significant signs of manipulation.";
        }


        document.getElementById("explanationText").innerText = explanation;


        let confidence = parseFloat(data.confidence);
        let startValue = 0;
        let endValue   = Math.round(confidence);
        let speed      = 12;

        /* =============================
           COLOR LOGIC (MATCHES BARS)
        ============================== */

        let circleColor = "";
        let glowClass   = "";

        if (data.label === "AI-Generated") {
            circleColor = "#a855f7";
            glowClass   = "glow-finish-high";
        }
        else if (data.label === "Manipulated") {
            circleColor = "#ff4d4d";
            glowClass   = "glow-finish-medium";
        }
        else {
            circleColor = "#00cc66";
            glowClass   = "glow-finish-low";
        }

        /* ============================= */

        let progress = setInterval(() => {

            startValue++;

            progressValue.textContent = startValue + "%";

            progressBar.style.background =
                `conic-gradient(${circleColor} ${startValue * 3.6}deg, #2a2a2a 0deg)`;

            if (startValue >= endValue) {

                clearInterval(progress);

                setTimeout(() => {

                    progressBar.classList.add(glowClass);

                    statusText.innerText = "Analysis Complete";
                    statusText.classList.add("analysis-visible");

                }, 200);
            }

        }, speed);


        /* =============================
           RISK BADGE
        ============================== */

        let riskText  = "";
        let riskClass = "";

        if (data.label === "AI-Generated") {
            riskText  = "HIGH RISK";
            riskClass = "risk-high";
        }
        else if (data.label === "Manipulated") {
            riskText  = "MEDIUM RISK";
            riskClass = "risk-medium";
        }
        else {
            riskText  = "LOW RISK";
            riskClass = "risk-low";
        }

        let riskElement = document.getElementById("riskLevel");
        riskElement.innerText = riskText;
        riskElement.className = "risk-badge " + riskClass;


        /* =============================
           TOP 3 PROBABILITY BARS
        ============================== */

        let top3HTML = "";

        data.top3.forEach(item => {

            let label   = item[0];
            let percent = parseFloat(item[1]).toFixed(2);

            let fillClass = "";

            if (label === "AI-Generated") {
                fillClass = "fill-ai";
            }
            else if (label === "Manipulated") {
                fillClass = "fill-manipulated";
            }
            else {
                fillClass = "fill-real";
            }

            top3HTML += `
                <div class="probability-item">
                    <div class="probability-label">
                        ${label} - ${percent}%
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${fillClass}"
                             style="width:${percent}%"></div>
                    </div>
                </div>
            `;
        });

        document.getElementById("top3").innerHTML = top3HTML;

        document.getElementById("caseIdText").innerText =
            "Case ID: " + data.case_id;

    })
    .catch(error => {
        console.error("Error:", error);
        alert("Something went wrong. Please try again.");
    });
}

/* =====================================================
   VIDEO PREDICTION FUNCTION
===================================================== */

function uploadVideo() {

    let file = document.getElementById("videoInput").files[0];

    if (!file) {
        alert("Please select a video!");
        return;
    }

    let formData = new FormData();
    formData.append("video", file);

    document.getElementById("videoResult").innerText = "";
    document.getElementById("videoLoader").style.display = "block";

    fetch("/video_predict", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {

        document.getElementById("videoLoader").style.display = "none";

        if (data.error) {
            document.getElementById("videoResult").innerText = data.error;
            return;
        }

        document.getElementById("videoResult").innerText =
            "Result: " + data.label + " | Confidence: " + data.confidence + "%";
    })
    .catch(error => {
        console.error("Error:", error);
        document.getElementById("videoResult").innerText = "Error processing video";
    });
}
function toggleVideoSidebar() {
    let panel = document.getElementById("videoSidebarPanel");

    panel.style.display =
        panel.style.display === "none" ? "block" : "none";
}
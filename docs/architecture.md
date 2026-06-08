# PenaltyIQ System Architecture

PenaltyIQ follows a decoupled, client-server architecture designed to separate the heavyweight AI vision processing from the mobile UI rendering.

## 🏗️ High-Level Diagram Description
The system is divided into three primary tiers:

1. **Presentation Tier (Flutter Mobile App)**
   - Responsible for real-time video capture at 60fps.
   - Manages UI states, user sessions, and API connectivity.
   - Receives the JSON analysis from the backend and renders a visual 2D skeleton overlay and graphical scoring charts.

2. **API & Orchestration Tier (FastAPI Backend)**
   - Acts as the central gateway for incoming video payloads.
   - Validates requests, authenticates sessions, and queues the video for the AI pipeline.
   - Built on ASGI for high-concurrency, non-blocking I/O during heavy processing.

3. **Biomechanical & AI Pipeline (Python Core)**
   - The heart of the system. Extracts video frames, maps 33 human joint coordinates, computes kinematic math, and matches data against physiological benchmarks.
   - Returns a structured JSON payload containing the technique score, kinematic deltas, and plain-English coaching cues.

## 🧠 Why Backend AI? (Separation of Concerns)
A key architectural decision was running **MediaPipe Pose** on the backend rather than directly on the user's smartphone. 

**Rationale:**
- **App Size:** Avoids shipping a 200MB+ AI model directly inside the Flutter app.
- **Consistency:** Ensures that the mathematical processing (which relies heavily on NumPy and SciPy) executes in a controlled, powerful server environment.
- **Upgradability:** Allows the engineering team to deploy new IK priors or model updates instantly without requiring users to download app updates from the App Store or Google Play.

## 💾 State & Data Flow
1. User records a 5-second penalty kick video.
2. Flutter App converts the video to a byte stream and POSTs it to the FastAPI endpoint.
3. FastAPI saves the stream to a temporary location and triggers the `core.coaching_engine`.
4. The processing pipeline returns a structured `AnalysisResponse` object.
5. FastAPI cleans up the temporary files and responds to the HTTP request.
6. Flutter parses the JSON and paints the biomechanical feedback on screen.

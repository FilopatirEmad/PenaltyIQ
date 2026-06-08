# 🧠 BACKEND DEEP DIVE: The PenaltyIQ Mentor Guide

Welcome. This is not just documentation — this is a masterclass in how the PenaltyIQ backend works. We are going to reverse-engineer the system together. By the end of this guide, you will understand exactly how raw pixels turn into professional biomechanical feedback. 

Grab a coffee. Let’s dive in.

---

## 1. 🔁 Execution Flow (CRITICAL)

Before looking at any math or code, you need to understand the pipeline. The backend is fundamentally a factory assembly line. Video goes in one end, JSON numbers come out the other.

### A. When `/process-video` is called

**What it does:** Extracts raw dots (coordinates) from the video. It doesn't do physics; it just finds the player and the ball.

**Execution Trace:**
1. **User:** Uploads `video.mp4` via the frontend.
2. **Route (`video_routes.py -> process_video`):** Receives the video file, session ID, and zone.
3. **Route Logic:** Writes the video to a temporary file on the server disk.
4. **Core Module (`pose_estimator.py -> PoseEstimator`):** Scans every frame of the video using Google's **MediaPipe**. Extracts 33 human joint coordinates (X, Y) per frame.
5. **Core Module (`ball_detector.py -> _stream_ball_detection`):** Scans the frames again using **OpenCV HoughCircles** to find the white pixels resembling a ball.
6. **Core Module (`calibration.py -> run_calibration_pipeline`):** Looks at the first few frames (the "T-pose" phase). Compares the physical size of the ball (pixels) to the human's thigh/trunk. Locks in a `scale_m_per_px` (how many pixels make a meter).
7. **Core Module (`ball_detector.py -> detect_contact_frame`):** Finds the exact frame where the ball first starts moving. This is "impact". 
8. **Route Logic:** Formats all this raw data (only keeping the frames *after* impact for analysis to save payload size) into a JSON.
9. **Output:** A huge JSON payload containing arrays of X,Y tracking data, sent back to the frontend.

### B. When `/analyze` is called

**What it does:** The heavy math. It takes the tracked dots, figures out what happened, and provides coaching tips.

**Execution Trace:**
1. **User (via Frontend App):** Sends the extracted JSON tracking data to `/analyze`.
2. **Route (`analysis_routes.py -> analyze`):** Receives the data (frames + calibration scale).
3. **Core (`signal_proc.py -> filter_landmark_trajectory`):** Cleans the data using a **Butterworth Filter**. (Raw video tracking is bumpy; this smooths it out).
4. **Core (`angle_calculator.py -> compute_joint_angles...`):** Converts the smoothed X,Y points of the hip, knee, and ankle into actual angles (e.g., knee bent at 45°).
5. **Core (`physics_engine.py -> run_physics_pipeline`):** Looks at the 4 frames of the ball immediately after the kick. Uses physics equations to calculate the initial velocity ($v_0$) and angle ($\theta$).
6. **Core (`ik_solver.py -> run_ik_pipeline`):** **Inverse Kinematics**. The solver asks: *"If the ball flew at 25 m/s, how did the human leg HAVE to move to generate that force?"* It calculates the biomechanical targets.
7. **Core (`digital_twin.py -> run_digital_twin`):** Takes the ball flight data, puts it in a virtual 3D simulation with air resistance, and sees if it hits the user's targeted zone.
8. **Core (`coaching_engine.py -> generate_full_coaching_report`):** Compares the *Actual Angles* (Step 4) against the *Target Angles* (Step 6). If they differ significantly, it creates a text string like "Keep your knee straighter."
9. **Output:** Final JSON string with physics metrics, scores, and coaching tips.

---

## 2. 📂 File-by-File Deep Dive

### `api/routes/video_routes.py`
* **Purpose:** The door that accepts heavy media uploads.
* **Key Function:** `process_video()`
  * *Input:* `UploadFile`
  * *Logic:* Memory management is critical here. It saves the uploaded stream to disk `tempfile.NamedTemporaryFile()`. It then runs the `PoseEstimator` and `ball_detector`, wrapping them in `asyncio.to_thread` to prevent the heavy CPU loop from freezing the entire FastAPI server.

### `api/routes/analysis_routes.py`
* **Purpose:** The maestro. Orchestrates the 6-stage mathematical pipeline.
* **Key Function:** `analyze()`
  * *Input:* `AnalysisRequest` schema (list of frames).
  * *Logic:* Encases each core stage in `try/except` blocks. If the physics engine fails (no ball detected), the route catches it, surfaces a pipeline warning, and fails gracefully. 

### `core/pose_estimator.py`
* **Purpose:** Wraps MediaPipe ML. 
* **Key Function:** `process_video_bytes_from_path(path)`
  * *Input:* Path to `video.mp4`.
  * *Logic:* Uses `cv2.VideoCapture` to loop frames. Feeds BGR image arrays into `mp_pose.process()`. Extracts the `.landmark` attributes.

### `core/signal_proc.py`
* **Purpose:** De-noising. High-speed cameras and ML produce "jitter" (pixels bounce around frame to frame).
* **Key Function:** `filter_landmark_trajectory(x_coords, y_coords)`
  * *Internal Logic:* Uses `scipy.signal.butter`. It creates a 2nd-order low-pass filter. 
  * *Analogy:* Imagine driving a car over a bumpy road. The raw tracker is the tires (bouncing everywhere). The Butterworth filter is the suspension, keeping the car body (the data) smooth. 

### `core/physics_engine.py`
* **Purpose:** Determines ball velocity from a sequence of pixels.
* **Key Function:** `run_physics_pipeline(ball_positions_px, scale, fps)`
  * *Math:* It takes $\Delta X$ and $\Delta Y$ over $\Delta t$ (time between frames based on FPS). Velocity is distance / time. Because it knows the calibration scale, it converts pixels to meters. $V = \frac{\text{Pixels} \times \text{Scale}}{\text{Time}}$.

### `core/ik_solver.py`
* **Purpose:** The hardest file in the system. Inverse Kinematics. 
* **Key Function:** `run_ik_pipeline(launch_target, player_segments)`
  * *Logic:* Uses `scipy.optimize.minimize`. It sets up an objective function: *"Find the joint angles that minimize the difference between the actual ball launch velocity and the theoretical velocity those joints would produce."* 
  * *Edge Cases:* Uses bounds from `constants/rom_limits.py` (Range of Motion). It prevents the solver from outputting physically impossible things (e.g., a knee bending backward 90 degrees) to achieve the math.

### `core/digital_twin.py`
* **Purpose:** Predicts future ball states. 
* **Key Function:** `run_digital_twin()`
  * *Logic:* Pure kinematics. $Z(t) = v_{0z} \times t$. $Y(t) = v_{0y} \times t - 0.5 \times g \times t^2$. It fast-forwards time ($t$) until the $Z$ distance matches the distance to the goal plane (usually 11 meters). It then checks the $Y$ position. If $Y < 2.44m$, it went under the crossbar!

---

## 3. 🧠 Core Algorithms Explained Simply

### Angle Calculation (Vector Math)
* **What it does:** Turns three dots (Hip, Knee, Ankle) into an angle (e.g., 45 degrees).
* **How:** Imagine drawing a straight line from Hip to Knee (Vector A), and Knee to Ankle (Vector B). It uses the **Dot Product** formula: $\quad \theta = \arccos(\frac{A \cdot B}{|A| |B|})$.
* **Why:** You can't give a player feedback saying *"Your ankle pixel was at 1024, 768"*. You must tell them *"Your knee was bent at 30 degrees."* 

### Inverse Kinematics (IK)
* **What it does:** Forward kinematics is "I move my arm; where is my hand?" Inverse kinematics is "I want my hand to be *there*; how do I need to move my arm?"
* **Why it's needed:** We know the *ball's* exit velocity. We want to know the *optimal* human body angles required to create that velocity over an idealized biomechanical system. 
* **Analogy:** IK is like reverse-engineering a cake. You taste the cake (the ball speed) and try to guess the recipe (the joint angles). The solver tries thousands of "recipes" in a split-second until it finds the one that bakes the exact cake it tasted.

---

## 4. 🔍 Important Code Patterns

1. **Stateless APIs:** You'll notice there is no `Database.save()` in the core logic. Data enters, computes, and leaves. This is brilliant because you can deploy this on AWS Lambda or Kubernetes. If 1,000 users upload a video, you can spin up 1,000 stateless instances without worrying about database locks.
2. **`asyncio.to_thread`:** FastAPI is asynchronous. But Python's math libraries (like OpenCV or Scipy) are **blocking CPU bound**. If you ran OpenCV directly in the route, the whole server would freeze for 3 seconds. By using `await asyncio.to_thread(run_physics...)`, FastAPI pushes the heavy math to a separate worker thread, allowing the main server loop to keep accepting new HTTP requests.
3. **Pydantic Schemas (`api/schemas/`):** The bouncer of the club. Before any JSON hits our math controllers, Pydantic verifies that `fps` is a float, `frames` is an array, etc. It fails fast if the frontend sends junk data.

---

## 5. 🧪 Trace a Real Example

**1. Input:** 
The router receives a payload: `hit_frame=40`. 
At frame 40, Ball is at (X=100, Y=100). 
At frame 41, Ball is at (X=120, Y=105). 
Scale: 1 Pixel = 0.05 meters. FPS = 60.

**2. Transformation (Physics Engine):**
$\Delta X = 20 \text{px} \times 0.05 = 1.0\text{m}$.
$\Delta Y = 5 \text{px} \times 0.05 = 0.25\text{m}$. 
$\Delta Time = 1/60 = 0.0166\text{s}$.
$V_x = 1.0 / 0.0166 = 60 \text{m/s}$
$V_y = 0.25 / 0.0166 = 15 \text{m/s}$
Total Velocity ($V_0$) = $\sqrt{60^2 + 15^2} = 61.8 \text{m/s}$ (Very fast kick!)

**3. Transformation (Coaching):**
Measured knee angle: 20°.
IK generated optimal target: 35°.
Delta: 15°.
Log generates: "Bend your knee more".

---

## 6. 🚨 Hidden Complexity (VERY IMPORTANT)

These are the silent traps in the codebase that will ruin your day if you ignore them:

* **The Butterworth "15 Frame Limit":** The filter (`signal_proc.py`) *requires* an array of at least 15 frames to work without blowing up the math. If you change the app to only record a 0.1-second video (6 frames at 60fps), the filter will crash.
* **OpenCV Memory Leaks:** Videos are huge. When reading `tmp.name` in OpenCV, if you don't call `cap.release()`, it will keep the file open in RAM. After 100 requests, the server will OOM (Out of Memory) crash. 
* **IK Local Minima:** `scipy.optimize` finds the *closest* answer, not always the *right* answer. If your physiological bounds (`rom_limits.py`) are set incorrectly, the math will trap itself in a "local minimum" producing weird feedback (like telling a player to have a 10-degree trunk when impossible).

---

## 7. 🔧 If I Want to Modify the System

* **Where do I add a new Coaching Rule?** 
  Go to `core/coaching_engine.py`. Find the threshold matrices inside `generate_full_coaching_report`. Add a new `if delta_deg > X:` check to append a new `CoachingFeedbackItem`.
* **Where do I add Spin dynamics to Physics?** 
  Go to `core/physics_engine.py` inside `run_physics_pipeline()`. Currently, it assumes simple projectile motion. You will need to add aerodynamic lift (Magnus effect) variables there.
* **Where do I change the JSON structure?** 
  Go to `api/schemas/analysis_schema.py`. You MUST change the Pydantic classes first. If you change a key in `routes` without changing the schema, the server will error out.

---

## 8. 🧠 Mental Model Summary

**The 5 Ideas You Must Never Forget:**
1. **The backend is a pure math pipe.** Pixels in, Vectors out. 
2. **FastAPI routes manage the traffic, but the `core/` folder is the brain.** Never put math inside `routes.py`.
3. **Scaling matters.** Images/Video are heavy. Always think "Is a gigabyte of RAM being held while I run this loop?" Use temp files and generators.
4. **Physical constraints.** Math is stupid. It will tell a human to extend their leg 5 meters if it solves an equation. Always bind IK solvers with biological reality.
5. **Fail gracefully.** If a player kicks a ball entirely out of frame, the ball tracker will fail. The system must catch this and return a warning JSON, not an HTTP 500 server crash.

---

## 🎁 BONUS: "If You Don't Understand This, You Will Break the System"

⚠️ **Never run OpenCV (`cv2`) or Scipy in the main thread space.** 
If you remove `await asyncio.to_thread(...)` from the route logic, you will block the Global Interpreter Lock (GIL). A single analysis request will literally stop the entire server from responding to *any* other user until the video is done processing. 

⚠️ **Do not misalign the Coordinate Systems**
MediaPipe provides Normalized Coordinates (0.0 to 1.0) where 0,0 is the top left. Ball tracking provides exact Pixel coordinates. In `extract_landmark_trajectories`, we multiply the Normalized coords by Width/Height *and* the `scale_m_per_px`. If you mess up this order of operations by a single decimal point, gravity will treat your 1.8-meter human as an 18-kilometer giant, and the physics solver will explode.
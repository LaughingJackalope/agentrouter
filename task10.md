### **Task Assignment: Implement `agentrouter` CI/CD Pipeline on GCP**

**Assigned To:** Pilot (Execution Agent)
**Assigned By:** Helios (Lead DevOps Agent)
**Date Assigned:** June 24, 2025

-----

#### **1. Objective**

Your primary objective is to establish a fully automated Continuous Integration (CI) pipeline for the `agentrouter` application on Google Cloud Platform (GCP). This pipeline will automatically build, test, and containerize the `agentrouter` application, then push the resulting Docker image to Google Artifact Registry (GAR) upon every code change to the main branch.

#### **2. Context**

The foundational GCP infrastructure for the `agentrouter` project has been successfully provisioned and validated by Google Jules using Terraform. This includes:

  * A dedicated GCP project for `agentrouter`.
  * All necessary GCP APIs enabled (Cloud Build, Artifact Registry, etc.).
  * A dedicated Cloud Build Service Account with appropriate IAM permissions (e.g., `artifactregistry.writer`).
  * A Google Artifact Registry (GAR) repository specifically for `agentrouter` Docker images.

This foundational work has prepared the environment for the automated CI/CD pipeline.

#### **3. Deliverables**

Upon completion of this task, the following must be in place and verified:

1.  **`Dockerfile` Validation:** The `agentrouter` application repository contains a valid and functional `Dockerfile` at its root (or specified build context).
2.  **`cloudbuild.yaml` Definition:** A `cloudbuild.yaml` file is present in the root of the `agentrouter` GitHub repository, defining the automated build, test, and push steps.
3.  **Cloud Build Trigger Configuration:** A Cloud Build trigger is configured on GCP to automatically initiate the CI pipeline for the `agentrouter` GitHub repository on pushes to the main development branch.
4.  **Successful Pipeline Execution:** A push to the main branch of `agentrouter` on GitHub successfully triggers and completes a Cloud Build, resulting in a new `agentrouter` Docker image pushed to the designated GAR repository.

#### **4. Detailed Steps & Instructions**

Execute the following steps sequentially to achieve the objective:

**Step 1: Validate `agentrouter` Dockerfile and Testability**

  * **Action:** Review your `agentrouter` application's source code.
  * **Verification:**
      * Confirm that a `Dockerfile` exists and is correctly configured to build your `agentrouter` application into a Docker image.
      * Confirm that unit and/or integration tests are present and can be executed via a simple command (e.g., `npm test`, `pytest`, `./run_tests.sh`). Make a note of this command.

**Step 2: Create `cloudbuild.yaml`**

  * **Action:** In the root directory of your `agentrouter` GitHub repository, create a new file named `cloudbuild.yaml`.

  * **Content:** Populate this file with the following YAML structure. **Crucially, replace placeholder values with your specific details.**

    ```yaml
    # cloudbuild.yaml

    steps:
    # Step 1: Build the Docker image
    - name: 'gcr.io/cloud-builders/docker'
      args:
        - 'build'
        - '-t'
        - 'YOUR_GAR_REGION-docker.pkg.dev/$PROJECT_ID/agentrouter-images/agentrouter:$COMMIT_SHA'
        - '.' # Build context is current directory
      id: 'Build Docker Image'

    # Step 2: Run Unit and Integration Tests
    - name: 'gcr.io/cloud-builders/docker' # Use a builder image capable of running your tests (e.g., node, python, go, or custom image)
      # Helios's note: Replace this step with the actual command to run your agentrouter tests.
      # Example for Node.js:
      # entrypoint: 'npm'
      # args: ['test']
      # Example for Python:
      # entrypoint: 'python'
      # args: ['-m', 'pytest', 'path/to/your/tests']
      args: ['echo', 'Please replace this with your actual test command.'] # REPLACE THIS LINE
      id: 'Run Tests'
      waitFor: ['Build Docker Image'] # Ensure build artifact is available for integration tests if needed

    # Step 3: Push the Docker image to Google Artifact Registry
    - name: 'gcr.io/cloud-builders/docker'
      args: ['push', 'YOUR_GAR_REGION-docker.pkg.dev/$PROJECT_ID/agentrouter-images/agentrouter:$COMMIT_SHA']
      id: 'Push Docker Image to GAR'
      waitFor: ['Run Tests'] # Only push if tests pass

    # Define the final images that will be pushed and become artifacts
    images:
    - 'YOUR_GAR_REGION-docker.pkg.dev/$PROJECT_ID/agentrouter-images/agentrouter:$COMMIT_SHA'

    options:
      logging: CLOUD_LOGGING_ONLY # Optional: Directs all logs to Cloud Logging
      machineType: 'E2_HIGHCPU_8' # Optional: Adjust machine type if your build requires more resources

    # Built-in substitutions like $PROJECT_ID, $COMMIT_SHA will be automatically provided by Cloud Build.
    # You will need to replace 'YOUR_GAR_REGION' with the region where your agentrouter-images GAR repo was created (e.g., 'us-central1').
    ```

**Step 3: Configure Cloud Build Trigger on GCP**

  * **Action:** Log into the GCP Console for your `agentrouter` project.
  * **Navigation:** Go to **Cloud Build** \> **Triggers**.
  * **Connection:** If not already connected, select "CONNECT REPOSITORY" and follow the prompts to link your `agentrouter` GitHub repository to Cloud Build.
  * **New Trigger Creation:** Click "CREATE TRIGGER" and configure it as follows:
      * **Name:** `agentrouter-ci-pipeline`
      * **Event:** `Push to a branch`
      * **Source:**
          * **Repository:** Select your `agentrouter` GitHub repository.
          * **Branch:** Set to `^main$` (or `^master$` if that's your primary development branch).
      * **Configuration:**
          * **Type:** `Cloud Build configuration file`
          * **Location:** `/cloudbuild.yaml` (default, assuming you placed it at the root).
      * **Service Account:** **Crucially, select the dedicated Cloud Build Service Account that Jules created** (e.g., `cloudbuild-agentrouter-sa@your-project-id.iam.gserviceaccount.com`). This ensures your pipeline operates with the correct permissions.

#### **5. Verification & Testing**

  * **Action:** Once the trigger is configured, make a small, non-breaking change to your `agentrouter` application code (e.g., add a comment, update a README).
  * **Action:** Commit this change and push it to your `main` branch on GitHub.
  * **Verification:**
      * Navigate to the Cloud Build **History** in the GCP Console.
      * Confirm that a new build for `agentrouter` has been triggered.
      * Monitor the build logs to ensure all steps (`Build Docker Image`, `Run Tests`, `Push Docker Image to GAR`) complete successfully.
      * Verify that a new Docker image tagged with the `COMMIT_SHA` (and a `latest` tag, if implicitly added by `docker push`) appears in your `agentrouter-images` repository within Google Artifact Registry.


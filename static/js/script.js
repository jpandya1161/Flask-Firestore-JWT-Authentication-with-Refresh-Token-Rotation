document.addEventListener("DOMContentLoaded", () => {
  // --- Login Page Logic ---
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const messageEl = document.getElementById("message");
      messageEl.style.display = "block";
      messageEl.className =
        "mt-4 text-center text-sm font-medium text-gray-600";
      messageEl.textContent = "Authenticating...";

      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      try {
        const response = await fetch("/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok) {
          messageEl.textContent = "Login successful! Redirecting...";
          messageEl.className =
            "mt-4 text-center text-sm font-medium text-green-600";

          // Client initiates the /refresh process immediately after login
          window.location.href = "/refresh";
        } else {
          messageEl.textContent = data.message || "Login failed.";
          messageEl.className =
            "mt-4 text-center text-sm font-medium text-red-600";
        }
      } catch (error) {
        messageEl.textContent = "Network error during login.";
        messageEl.className =
          "mt-4 text-center text-sm font-medium text-red-600";
        console.error("Error:", error);
      }
    });
  }

  // --- Dashboard Page Logic ---
  const timerEl = document.getElementById("timer");
  const protectedDataButton = document.getElementById("protectedDataButton");

  if (timerEl) {
    // Reads the initial time from the rendered HTML (which received it from Flask)
    // Note: The timer starts at the full 5 minutes every time the page loads.
    let expirationSeconds = 300;

    function fetchProtectedData() {
      const dataEl = document.getElementById("data-display");
      dataEl.textContent = "Fetching data...";

      // This is just a simple fetch to the dashboard route itself, which triggers validation
      fetch("/dashboard")
        .then((response) => {
          const status = response.status;

          if (response.ok) {
            // 200 OK
            dataEl.innerHTML =
              '<span class="text-green-600">Successfully accessed protected data!</span>';
          } else if (status === 302) {
            // 302 Redirect means the token expired and server is initiating refresh
            dataEl.innerHTML =
              '<span class="text-yellow-600">Access Token Expired! Server is attempting silent refresh...</span>';
            setTimeout(() => {
              // Reload the page to complete the server-side redirect chain (/dashboard -> /refresh -> /dashboard)
              window.location.reload();
            }, 1000);
          } else {
            // 401 Unauthorized or other error
            dataEl.innerHTML =
              '<span class="text-red-600">Access Denied/Session Ended.</span>';
          }
        })
        .catch((error) => {
          dataEl.innerHTML = '<span class="text-red-600">Network error.</span>';
          console.error("Fetch error:", error);
        });
    }

    if (protectedDataButton) {
      protectedDataButton.addEventListener("click", fetchProtectedData);
    }

    function updateExpirationTimer() {
      if (expirationSeconds > 0) {
        expirationSeconds--;
        const minutes = Math.floor(expirationSeconds / 60);
        const seconds = expirationSeconds % 60;
        timerEl.textContent = `Access Token expires in: ${minutes}:${
          seconds < 10 ? "0" : ""
        }${seconds}`;
        setTimeout(updateExpirationTimer, 1000);
      } else {
        timerEl.textContent =
          "Access Token has EXPIRED! Next navigation/refresh will trigger silent re-login.";
        timerEl.className = "text-red-500 font-bold";
      }
    }

    // Start the timer when the dashboard loads
    updateExpirationTimer();
  }
});

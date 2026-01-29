document.addEventListener("DOMContentLoaded", function () {
  checkAllEndpoints();
});

function checkAllEndpoints() {
  var cards = document.querySelectorAll(".status-card");
  cards.forEach(function (card) {
    checkEndpoint(card.dataset.endpointId);
  });
}

function checkEndpoint(endpointId) {
  setCardLoading(endpointId, true);

  fetch("/status/api/check/" + endpointId)
    .then(function (res) {
      return res.json();
    })
    .then(function (result) {
      updateCard(result);
    })
    .catch(function (err) {
      console.error("Error checking endpoint " + endpointId + ":", err);
      setCardLoading(endpointId, false);
    });
}

function setCardLoading(endpointId, loading) {
  var card = document.querySelector(
    '.status-card[data-endpoint-id="' + endpointId + '"]'
  );
  if (!card) return;

  var overlay = card.querySelector(".loading-overlay");
  if (overlay) {
    overlay.style.display = loading ? "flex" : "none";
  }

  if (loading) {
    card.classList.remove("border-success", "border-danger");
    card.classList.add("border-secondary");
  }
}

function updateCard(result) {
  var card = document.querySelector(
    '.status-card[data-endpoint-id="' + result.endpoint_id + '"]'
  );
  if (!card) return;

  // Hide loading overlay
  var overlay = card.querySelector(".loading-overlay");
  if (overlay) {
    overlay.style.display = "none";
  }

  // Update border color
  card.classList.remove("border-success", "border-danger", "border-secondary");
  card.classList.add(result.is_healthy ? "border-success" : "border-danger");

  // Update status badge
  var badge = card.querySelector(".status-badge");
  if (badge) {
    badge.textContent = result.status;
    badge.className = "badge status-badge " + (result.is_healthy ? "bg-success" : "bg-danger");
  }

  // Update metrics
  var latencyEl = card.querySelector(".metric-latency");
  if (latencyEl) {
    latencyEl.textContent = result.latency_display;
  }

  var codeEl = card.querySelector(".metric-code");
  if (codeEl) {
    codeEl.textContent = result.status_code_display;
  }

  var urlEl = card.querySelector(".metric-url");
  if (urlEl) {
    urlEl.textContent = result.url;
  }

  // Update error section
  var errorSection = card.querySelector(".error-section");
  if (errorSection) {
    if (result.error) {
      errorSection.style.display = "block";
      var errorText = errorSection.querySelector(".error-text");
      if (errorText) {
        errorText.textContent = result.error;
      }
    } else {
      errorSection.style.display = "none";
    }
  }

  // Update card timestamp
  var tsEl = card.querySelector(".card-timestamp");
  if (tsEl) {
    tsEl.textContent = result.checked_at;
  }
}

(function () {
  var EYE =
    '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>';
  var EYE_OFF =
    '<path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a18.45 18.45 0 0 1 5.06-5.94"/>' +
    '<path d="M9.9 4.24A10.94 10.94 0 0 1 12 5c7 0 11 7 11 7a18.5 18.5 0 0 1-2.16 3.19"/>' +
    '<path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/>' +
    '<line x1="1" y1="1" x2="23" y2="23"/>';

  function setVisible(input, button, icon, visible) {
    input.type = visible ? "text" : "password";
    button.setAttribute("aria-pressed", visible ? "true" : "false");
    button.setAttribute(
      "aria-label",
      visible ? "Hide password" : "Show password"
    );
    icon.innerHTML = visible ? EYE_OFF : EYE;
  }

  document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
    var wrap = button.closest(".password-field");
    if (!wrap) return;
    var input = wrap.querySelector("input");
    var icon = button.querySelector("svg");
    if (!input || !icon) return;

    setVisible(input, button, icon, false);

    button.addEventListener("click", function () {
      setVisible(input, button, icon, input.type === "password");
    });
  });
})();

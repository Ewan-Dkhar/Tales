/* One orchestrated moment: the ghost speaks its first line once, on load.
   Nothing else on this page animates. Content is in the HTML already, so a
   reader without JavaScript sees the whole sentence immediately. */

(function () {
  "use strict";

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* --- the revelation ---------------------------------------------------- */
  function speak() {
    var stream = document.querySelector(".ghost-quote .stream");
    if (!stream || reduce.matches) return;

    var text = stream.textContent.trim();
    var words = text.split(/\s+/);
    stream.textContent = "";

    var spans = words.map(function (word, i) {
      var span = document.createElement("span");
      span.textContent = word;
      stream.appendChild(span);
      if (i < words.length - 1) stream.appendChild(document.createTextNode(" "));
      return span;
    });

    var cursor = document.createElement("span");
    cursor.className = "cursor";
    cursor.setAttribute("aria-hidden", "true");
    stream.parentNode.appendChild(cursor);

    stream.setAttribute("data-revealing", "");

    var i = 0;
    var step = function () {
      if (i < spans.length) {
        spans[i].classList.add("on");
        if (i === 0) cursor.style.opacity = "1";
        i += 1;
        window.setTimeout(step, 78 + Math.random() * 46);
      } else {
        cursor.classList.add("blink");
        window.setTimeout(function () {
          cursor.style.opacity = "0";
        }, 2300);
      }
    };

    window.setTimeout(step, 260);
  }

  /* --- copying the install block ----------------------------------------- */
  function wireCopy() {
    var buttons = document.querySelectorAll(".copy");
    var statusEl = document.getElementById("copy-status");
    var status = {
      set textContent(value) {
        if (statusEl) statusEl.textContent = value;
      }
    };
    Array.prototype.forEach.call(buttons, function (button) {
      button.addEventListener("click", function () {
        var target = document.getElementById(button.getAttribute("data-copy"));
        if (!target) return;

        var text = Array.prototype.map
          .call(target.childNodes, function (node) {
            return node.textContent;
          })
          .join("")
          .replace(/^\s*\$ /gm, "")
          .replace(/^# .*$/gm, "")
          .replace(/\n{3,}/g, "\n\n")
          .trim();

        var done = function () {
          button.textContent = "Copied";
          button.setAttribute("data-done", "1");
          status.textContent = "Install commands copied to the clipboard.";
          window.setTimeout(function () {
            button.textContent = "Copy";
            button.removeAttribute("data-done");
          }, 1800);
        };

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, function () {
            button.textContent = "Select it";
            status.textContent = "Copying was blocked. Select the block and copy it by hand.";
          });
        } else {
          var range = document.createRange();
          range.selectNodeContents(target);
          var sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
          button.textContent = "Press ⌘C";
          status.textContent = "The block is selected. Press Command C or Control C to copy.";
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      speak();
      wireCopy();
    });
  } else {
    speak();
    wireCopy();
  }
})();

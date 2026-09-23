(function () {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var preloader = document.querySelector(".preloader");
    var themeBtn = document.querySelector(".theme");
    var root = document.documentElement;
    var deck = document.querySelector(".deck");
    var railGlass = document.querySelector(".rail-glass");
    var railBar = document.querySelector(".rail-bar");

    function setTheme(name) {
        root.setAttribute("data-theme", name);
        try { localStorage.setItem("rypt-theme", name); } catch (e) {}
    }

    function endRadius(x, y) {
        return Math.hypot(
            Math.max(x, window.innerWidth - x),
            Math.max(y, window.innerHeight - y)
        );
    }

    function toggleTheme(event) {
        var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
        if (reduce) {
            setTheme(next);
            return;
        }
        var x = event.clientX;
        var y = event.clientY;
        var radius = endRadius(x, y);
        if (document.startViewTransition) {
            var transition = document.startViewTransition(function () {
                setTheme(next);
            });
            transition.ready.then(function () {
                root.animate(
                    {
                        clipPath: [
                            "circle(0px at " + x + "px " + y + "px)",
                            "circle(" + radius + "px at " + x + "px " + y + "px)"
                        ]
                    },
                    {
                        duration: 720,
                        easing: "cubic-bezier(0.76, 0, 0.24, 1)",
                        pseudoElement: "::view-transition-new(root)"
                    }
                );
            });
            return;
        }
        var overlay = document.createElement("div");
        overlay.className = "theme-wipe";
        overlay.style.background = next === "light" ? "#e8e8e8" : "#222222";
        overlay.style.clipPath = "circle(0px at " + x + "px " + y + "px)";
        document.body.appendChild(overlay);
        requestAnimationFrame(function () {
            overlay.style.clipPath = "circle(" + radius + "px at " + x + "px " + y + "px)";
        });
        overlay.addEventListener("transitionend", function () {
            setTheme(next);
            overlay.remove();
        }, { once: true });
    }

    if (themeBtn) themeBtn.addEventListener("click", toggleTheme);

    if (railGlass && !reduce) {
        railGlass.addEventListener("pointermove", function (event) {
            var box = railGlass.getBoundingClientRect();
            railGlass.style.setProperty("--gx", (event.clientX - box.left) + "px");
            railGlass.style.setProperty("--gy", (event.clientY - box.top) + "px");
        });
    }

    function hidePreloader() {
        if (!preloader) return;
        preloader.classList.add("is-gone");
        preloader.style.display = "none";
    }

    function startDeck() {
        if (!deck) return;
        var originals = Array.prototype.slice.call(deck.querySelectorAll(".slide"));
        var n = originals.length;
        if (!n) return;
        var start = parseInt(deck.getAttribute("data-index") || "0", 10);
        if (isNaN(start) || start < 0 || start >= n) start = 0;

        var firstClone = originals[0].cloneNode(true);
        var lastClone = originals[n - 1].cloneNode(true);
        firstClone.setAttribute("aria-hidden", "true");
        lastClone.setAttribute("aria-hidden", "true");
        firstClone.querySelectorAll("[data-russia-map]").forEach(function (el) {
            delete el.dataset.ready;
        });
        lastClone.querySelectorAll("[data-russia-map]").forEach(function (el) {
            delete el.dataset.ready;
        });
        deck.appendChild(firstClone);
        deck.insertBefore(lastClone, originals[0]);

        var pos = start + 1;
        var moving = false;

        function apply(animate) {
            if (animate && !reduce) deck.classList.add("is-moving");
            else deck.classList.remove("is-moving");
            deck.style.transform = "translate3d(" + (-pos * 100) + "vw,0,0)";
        }

        function realIndex() {
            if (pos === 0) return n - 1;
            if (pos === n + 1) return 0;
            return pos - 1;
        }

        function syncChrome() {
            var i = realIndex();
            var slide = originals[i];
            if (slide && slide.dataset.title) document.title = slide.dataset.title;
            if (railBar) {
                Array.prototype.forEach.call(railBar.querySelectorAll("a[data-slide]"), function (a) {
                    a.classList.toggle("is-now", a.getAttribute("data-slide") === String(i));
                });
            }
        }

        function go(nextPos, animate) {
            if (moving && animate) return;
            pos = nextPos;
            var canAnimate = animate && !reduce;
            if (canAnimate) moving = true;
            apply(canAnimate);
            if (!canAnimate) {
                if (pos === 0) pos = n;
                else if (pos === n + 1) pos = 1;
                apply(false);
            }
            syncChrome();
            var i = realIndex();
            var slide = originals[i];
            if (slide && slide.dataset.url) {
                var nextUrl = slide.dataset.url;
                if (window.location.pathname !== nextUrl) {
                    history.pushState({ pos: pos }, "", nextUrl);
                }
            }
        }

        deck.addEventListener("transitionend", function (event) {
            if (event.target !== deck || event.propertyName !== "transform") return;
            moving = false;
            if (pos === 0) {
                pos = n;
                apply(false);
            } else if (pos === n + 1) {
                pos = 1;
                apply(false);
            }
        });

        apply(false);
        syncChrome();

        document.querySelectorAll(".flip-prev").forEach(function (btn) {
            btn.addEventListener("click", function () { go(pos - 1, true); });
        });
        document.querySelectorAll(".flip-next").forEach(function (btn) {
            btn.addEventListener("click", function () { go(pos + 1, true); });
        });

        if (railBar) {
            railBar.addEventListener("click", function (event) {
                var a = event.target.closest("a[data-slide]");
                if (!a) return;
                event.preventDefault();
                var i = parseInt(a.getAttribute("data-slide"), 10);
                if (isNaN(i)) return;
                go(i + 1, true);
            });
        }

        var brand = document.querySelector(".chrome .brand");
        if (brand) {
            brand.addEventListener("click", function (event) {
                event.preventDefault();
                go(1, true);
            });
        }

        document.addEventListener("keydown", function (event) {
            if (event.target && /input|textarea|select/i.test(event.target.tagName)) return;
            if (event.key === "ArrowLeft") {
                event.preventDefault();
                go(pos - 1, true);
            }
            if (event.key === "ArrowRight") {
                event.preventDefault();
                go(pos + 1, true);
            }
        });

        var startX = 0;
        var startY = 0;
        var tracking = false;
        deck.addEventListener("pointerdown", function (event) {
            if (event.pointerType === "mouse") return;
            tracking = true;
            startX = event.clientX;
            startY = event.clientY;
        });
        window.addEventListener("pointerup", function (event) {
            if (!tracking) return;
            tracking = false;
            var dx = event.clientX - startX;
            var dy = event.clientY - startY;
            if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 1.6) return;
            if (dx < 0) go(pos + 1, true);
            else go(pos - 1, true);
        });

        window.addEventListener("popstate", function () {
            var path = window.location.pathname;
            var i = originals.findIndex(function (slide) {
                return slide.dataset.url === path || (path === "/" && slide.dataset.url === "/");
            });
            if (i < 0) return;
            pos = i + 1;
            apply(false);
            syncChrome();
        });
    }

    function startSeasonTabs() {
        var root = document.querySelector("[data-season-tabs]");
        if (!root) return;
        var tabs = Array.prototype.slice.call(root.querySelectorAll("[role=tab]"));
        var panels = Array.prototype.slice.call(root.querySelectorAll("[role=tabpanel]"));
        if (!tabs.length) return;

        function show(name, updateHash) {
            var found = false;
            tabs.forEach(function (tab) {
                var on = tab.getAttribute("data-tab") === name;
                tab.setAttribute("aria-selected", on ? "true" : "false");
                tab.tabIndex = on ? 0 : -1;
                if (on) found = true;
            });
            if (!found) {
                name = tabs[0].getAttribute("data-tab");
                tabs[0].setAttribute("aria-selected", "true");
                tabs[0].tabIndex = 0;
            }
            panels.forEach(function (panel) {
                var on = panel.id === "panel-" + name;
                if (on) panel.removeAttribute("hidden");
                else panel.setAttribute("hidden", "");
            });
            if (updateHash) {
                var next = "#" + name;
                if (window.location.hash !== next) {
                    history.replaceState(null, "", next);
                }
            }
        }

        var initial = (window.location.hash || "").replace("#", "");
        show(initial || tabs[0].getAttribute("data-tab"), false);

        root.addEventListener("click", function (event) {
            var tab = event.target.closest("[role=tab]");
            if (!tab || !root.contains(tab)) return;
            show(tab.getAttribute("data-tab"), true);
        });

        root.addEventListener("keydown", function (event) {
            var tab = event.target.closest("[role=tab]");
            if (!tab || !root.contains(tab)) return;
            var i = tabs.indexOf(tab);
            if (i < 0) return;
            var next = i;
            if (event.key === "ArrowRight" || event.key === "ArrowDown") next = (i + 1) % tabs.length;
            else if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = (i - 1 + tabs.length) % tabs.length;
            else if (event.key === "Home") next = 0;
            else if (event.key === "End") next = tabs.length - 1;
            else return;
            event.preventDefault();
            tabs[next].focus();
            show(tabs[next].getAttribute("data-tab"), true);
        });

        window.addEventListener("hashchange", function () {
            show((window.location.hash || "").replace("#", ""), false);
        });
    }

    function startPhotoStudio() {
        var root = document.querySelector("[data-photo-studio]");
        if (!root) return;

        var switches = Array.prototype.slice.call(root.querySelectorAll("[data-album-view]"));
        var panes = Array.prototype.slice.call(root.querySelectorAll("[data-album-pane]"));
        function showAlbum(name) {
            switches.forEach(function (btn) {
                var on = btn.getAttribute("data-album-view") === name;
                btn.classList.toggle("is-on", on);
                btn.setAttribute("aria-selected", on ? "true" : "false");
            });
            panes.forEach(function (pane) {
                var on = pane.getAttribute("data-album-pane") === name;
                if (on) pane.removeAttribute("hidden");
                else pane.setAttribute("hidden", "");
            });
        }
        switches.forEach(function (btn) {
            btn.addEventListener("click", function () {
                showAlbum(btn.getAttribute("data-album-view"));
            });
        });

        var thumbs = Array.prototype.slice.call(root.querySelectorAll(".photo-thumb"));
        var frame = root.querySelector(".photo-frame img");
        var caption = root.querySelector(".photo-frame figcaption");
        var count = root.querySelector("[data-photo-count]");
        var original = root.querySelector("[data-photo-original]");
        var prev = root.querySelector(".photo-prev");
        var next = root.querySelector(".photo-next");
        if (!thumbs.length || !frame) return;
        var index = 0;

        function show(i) {
            if (!thumbs.length) return;
            index = (i + thumbs.length) % thumbs.length;
            var thumb = thumbs[index];
            frame.src = thumb.getAttribute("data-src") || "";
            frame.alt = thumb.getAttribute("aria-label") || "";
            frame.referrerPolicy = "no-referrer";
            if (caption) caption.textContent = thumb.getAttribute("data-caption") || "";
            if (count) count.textContent = (index + 1) + " / " + thumbs.length;
            if (original) {
                var href = thumb.getAttribute("data-original") || "";
                original.href = href;
                original.hidden = !href;
            }
            thumbs.forEach(function (el, n) {
                el.classList.toggle("is-on", n === index);
            });
        }

        thumbs.forEach(function (thumb, i) {
            thumb.addEventListener("click", function () {
                show(i);
                showAlbum("carousel");
            });
        });
        if (prev) prev.addEventListener("click", function () { show(index - 1); });
        if (next) next.addEventListener("click", function () { show(index + 1); });
        show(0);
    }

    startDeck();
    startSeasonTabs();
    startPhotoStudio();

    function parseJsonScript(root, selector) {
        var node = root.querySelector(selector);
        if (!node) return {};
        try {
            return JSON.parse(node.textContent || "{}");
        } catch (e) {
            return {};
        }
    }

    function initRussiaMap(root) {
        if (!root || root.dataset.ready === "1") return;
        var svg = root.querySelector("svg");
        var panel = root.querySelector("[data-russia-panel]");
        if (!svg || !panel) return;
        root.dataset.ready = "1";

        var data = parseJsonScript(root, "[data-russia-data]");
        var names = parseJsonScript(root, "[data-russia-names]");
        var empty = panel.querySelector("[data-russia-empty]");
        var body = panel.querySelector("[data-russia-body]");
        var viewport = root.querySelector("[data-russia-viewport]");
        var zoomLayer = root.querySelector("[data-russia-zoom]");
        var activePath = null;
        var lockedCode = null;

        // —— масштаб / сдвиг ——
        var scale = 1;
        var tx = 0;
        var ty = 0;
        var minScale = 1;
        var maxScale = 6;
        var dragging = false;
        var moved = false;
        var lastX = 0;
        var lastY = 0;
        var pendingCode = null;

        function regionFromEventTarget(target) {
            if (!target) return null;
            if (target.classList && target.classList.contains("russia-region")) return target;
            if (typeof target.closest === "function") return target.closest(".russia-region");
            return null;
        }

        function applyZoom() {
            if (!zoomLayer) return;
            zoomLayer.style.transform =
                "translate(" + tx + "px," + ty + "px) scale(" + scale + ")";
        }

        function clampPan() {
            if (!viewport) return;
            var rect = viewport.getBoundingClientRect();
            var w = rect.width;
            var h = rect.height;
            var maxX = 0;
            var maxY = 0;
            var minX = w * (1 - scale);
            var minY = h * (1 - scale);
            if (scale <= 1) {
                tx = 0;
                ty = 0;
                return;
            }
            tx = Math.min(maxX, Math.max(minX, tx));
            ty = Math.min(maxY, Math.max(minY, ty));
        }

        function zoomAt(clientX, clientY, nextScale) {
            if (!viewport) return;
            nextScale = Math.min(maxScale, Math.max(minScale, nextScale));
            if (nextScale === scale) return;
            var rect = viewport.getBoundingClientRect();
            var x = clientX - rect.left;
            var y = clientY - rect.top;
            // точка под курсором в координатах слоя до зума
            var sx = (x - tx) / scale;
            var sy = (y - ty) / scale;
            scale = nextScale;
            tx = x - sx * scale;
            ty = y - sy * scale;
            clampPan();
            applyZoom();
        }

        function resetZoom() {
            scale = 1;
            tx = 0;
            ty = 0;
            applyZoom();
        }

        if (viewport && zoomLayer) {
            viewport.addEventListener(
                "wheel",
                function (event) {
                    event.preventDefault();
                    var factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
                    zoomAt(event.clientX, event.clientY, scale * factor);
                },
                { passive: false }
            );

            viewport.addEventListener("pointerdown", function (event) {
                if (event.button !== 0) return;
                if (event.target.closest && event.target.closest(".russia-zoom-bar")) return;
                dragging = true;
                moved = false;
                lastX = event.clientX;
                lastY = event.clientY;
                var regionEl = regionFromEventTarget(event.target);
                pendingCode = regionEl ? regionEl.id : null;
                viewport.classList.add("is-panning");
                try {
                    viewport.setPointerCapture(event.pointerId);
                } catch (e) {}
            });

            viewport.addEventListener("pointermove", function (event) {
                if (!dragging) return;
                var dx = event.clientX - lastX;
                var dy = event.clientY - lastY;
                if (Math.abs(dx) + Math.abs(dy) > 4) moved = true;
                lastX = event.clientX;
                lastY = event.clientY;
                if (scale <= 1) return;
                tx += dx;
                ty += dy;
                clampPan();
                applyZoom();
            });

            function endPan(event) {
                if (!dragging) return;
                dragging = false;
                viewport.classList.remove("is-panning");
                try {
                    viewport.releasePointerCapture(event.pointerId);
                } catch (e) {}
                // pointer capture ломает click на SVG path — фиксируем/снимаем здесь
                if (!moved && pendingCode) {
                    if (lockedCode === pendingCode) {
                        // Повторный клик — снять фикс, снова работает наведение
                        lockedCode = null;
                        selectRegion(pendingCode, svg.getElementById(pendingCode));
                    } else {
                        lockedCode = pendingCode;
                        selectRegion(pendingCode, svg.getElementById(pendingCode));
                    }
                }
                pendingCode = null;
            }

            viewport.addEventListener("pointerup", endPan);
            viewport.addEventListener("pointercancel", endPan);

            var btnIn = root.querySelector("[data-russia-zoom-in]");
            var btnOut = root.querySelector("[data-russia-zoom-out]");
            var btnReset = root.querySelector("[data-russia-zoom-reset]");
            if (btnIn) {
                btnIn.addEventListener("click", function () {
                    var rect = viewport.getBoundingClientRect();
                    zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, scale * 1.25);
                });
            }
            if (btnOut) {
                btnOut.addEventListener("click", function () {
                    var rect = viewport.getBoundingClientRect();
                    zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, scale / 1.25);
                });
            }
            if (btnReset) btnReset.addEventListener("click", resetZoom);
            applyZoom();
        }

        Object.keys(data).forEach(function (code) {
            if (!data[code] || !data[code].has_tournament) return;
            var path = svg.getElementById(code);
            if (path) path.classList.add("has-tournament");
        });

        function field(name) {
            return body.querySelector('[data-f="' + name + '"]');
        }

        function showBlock(name, on) {
            var el = body.querySelector('[data-block="' + name + '"]');
            if (el) el.classList.toggle("is-hidden", !on);
        }

        function selectRegion(code, path) {
            if (activePath) activePath.classList.remove("is-active");
            activePath = path || svg.getElementById(code);
            if (activePath) activePath.classList.add("is-active");

            empty.classList.add("is-hidden");
            body.classList.remove("is-hidden");

            var card = data[code];
            var regionName = (card && card.region) || names[code] || code;
            field("region").textContent = regionName;

            if (!card) {
                field("title").textContent = regionName;
                field("meta").textContent = "";
                showBlock("contacts", false);
                showBlock("info", false);
                showBlock("problems", false);
                showBlock("results", false);
                showBlock("photos", false);
                showBlock("none", true);
                return;
            }

            field("title").textContent = card.title || regionName;
            var metaParts = [];
            if (card.city) metaParts.push(card.city);
            if (card.when) metaParts.push(card.when);
            field("meta").textContent = metaParts.join(" · ");

            var hasContacts = !!(card.contacts && String(card.contacts).trim());
            showBlock("contacts", hasContacts);
            if (hasContacts) field("contacts").textContent = card.contacts;

            var hasInfo = !!(card.info_html && String(card.info_html).trim());
            showBlock("info", hasInfo);
            if (hasInfo) field("info").innerHTML = card.info_html;

            var problems = card.problems || [];
            showBlock("problems", problems.length > 0);
            var ol = field("problems");
            ol.innerHTML = "";
            problems.forEach(function (p) {
                var li = document.createElement("li");
                var strong = document.createElement("strong");
                strong.textContent = p.title || "";
                li.appendChild(strong);
                if (p.statement) {
                    var st = document.createElement("span");
                    st.className = "st";
                    st.textContent = p.statement;
                    li.appendChild(st);
                }
                ol.appendChild(li);
            });

            var hasResultsText = !!(card.results_text && String(card.results_text).trim());
            var hasResultsUrl = !!(card.results_url && String(card.results_url).trim());
            showBlock("results", hasResultsText || hasResultsUrl);
            field("results_text").textContent = hasResultsText ? card.results_text : "";
            field("results_text").style.display = hasResultsText ? "" : "none";
            var link = field("results_link");
            if (hasResultsUrl) {
                link.href = card.results_url;
                link.textContent = card.results_label || "Оригинал результатов";
                link.style.display = "";
            } else {
                link.removeAttribute("href");
                link.textContent = "";
                link.style.display = "none";
            }

            var photos = card.photos || [];
            showBlock("photos", photos.length > 0);
            var gallery = field("photos");
            gallery.innerHTML = "";
            photos.forEach(function (ph) {
                var a = document.createElement("a");
                a.href = ph.original || ph.src;
                a.target = "_blank";
                a.rel = "noreferrer";
                if (ph.caption) a.title = ph.caption;
                var img = document.createElement("img");
                img.src = ph.thumb || ph.src;
                img.alt = ph.caption || "";
                a.appendChild(img);
                gallery.appendChild(a);
            });

            showBlock("none", false);
        }

        svg.querySelectorAll(".russia-region").forEach(function (path) {
            var code = path.id;
            if (!code) return;
            path.setAttribute("role", "button");
            path.setAttribute("aria-label", names[code] || code);

            // Наведение подсвечивает; панель меняет, только если нет фикса.
            path.addEventListener("mouseenter", function () {
                path.classList.add("is-hover");
                if (!lockedCode) {
                    selectRegion(code, path);
                }
            });
            path.addEventListener("mouseleave", function () {
                path.classList.remove("is-hover");
            });
        });
    }

    function initAllRussiaMaps() {
        document.querySelectorAll("[data-russia-map]").forEach(initRussiaMap);
    }

    initAllRussiaMaps();

    if (!preloader || reduce || typeof anime === "undefined") {
        hidePreloader();
        return;
    }

    var orb = preloader.querySelector(".preloader-orb");
    anime.timeline({ easing: "easeInOutCubic" })
        .add({
            targets: orb,
            scale: [0.15, 1.2, 1],
            duration: 680
        })
        .add({
            targets: preloader,
            clipPath: ["circle(150% at 50% 50%)", "circle(0% at 50% 50%)"],
            duration: 780,
            complete: hidePreloader
        });
})();

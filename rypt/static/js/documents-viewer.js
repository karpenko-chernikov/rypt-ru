/**
 * Просмотр документов: PDF.js (fit-width, непрерывный скролл) и HTML-устав в том же контейнере.
 * Стандартный подход вместо native PDF iframe (ломает клики/масштаб/плотность).
 */
(function () {
    var PDFJS_VER = "4.10.38";
    var PDFJS_CDN = "https://cdn.jsdelivr.net/npm/pdfjs-dist@" + PDFJS_VER;
    var pdfjsLibPromise = null;

    function loadPdfJs() {
        if (pdfjsLibPromise) return pdfjsLibPromise;
        // dynamic import — ESM-сборка pdfjs с CDN
        pdfjsLibPromise = import(/* webpackIgnore: true */ PDFJS_CDN + "/build/pdf.mjs").then(
            function (pdfjsLib) {
                pdfjsLib.GlobalWorkerOptions.workerSrc =
                    PDFJS_CDN + "/build/pdf.worker.min.mjs";
                return pdfjsLib;
            }
        );
        return pdfjsLibPromise;
    }

    function debounce(fn, ms) {
        var t = 0;
        return function () {
            var ctx = this;
            var args = arguments;
            clearTimeout(t);
            t = setTimeout(function () {
                fn.apply(ctx, args);
            }, ms);
        };
    }

    async function mountPdf(host, url) {
        if (host.dataset.ready === "1") return;
        host.dataset.ready = "1";
        host.classList.add("is-loading");
        host.setAttribute("aria-busy", "true");

        var pdfjsLib = await loadPdfJs();
        var pdf = await pdfjsLib.getDocument({ url: url, withCredentials: false }).promise;
        var lastWidth = 0;
        var pagesEl = document.createElement("div");
        pagesEl.className = "documents-pdf-pages";
        host.innerHTML = "";
        host.appendChild(pagesEl);

        async function renderAll() {
            // Вся ширина вьюера: страница масштабируется под контейнер (fit-width).
            var width = Math.floor(host.clientWidth - 16);
            if (width < 40) return;
            if (Math.abs(width - lastWidth) < 6 && pagesEl.childElementCount) return;
            lastWidth = width;

            var frag = document.createDocumentFragment();
            for (var n = 1; n <= pdf.numPages; n++) {
                var page = await pdf.getPage(n);
                var base = page.getViewport({ scale: 1 });
                var scale = width / base.width;
                var viewport = page.getViewport({ scale: scale });
                var outputScale = window.devicePixelRatio || 1;

                var canvas = document.createElement("canvas");
                canvas.className = "documents-pdf-page";
                canvas.width = Math.floor(viewport.width * outputScale);
                canvas.height = Math.floor(viewport.height * outputScale);
                canvas.style.width = Math.floor(viewport.width) + "px";
                canvas.style.height = Math.floor(viewport.height) + "px";
                canvas.setAttribute("aria-label", "Страница " + n + " из " + pdf.numPages);

                var ctx = canvas.getContext("2d");
                var transform = outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null;
                await page.render({
                    canvasContext: ctx,
                    viewport: viewport,
                    transform: transform,
                }).promise;

                frag.appendChild(canvas);
            }
            pagesEl.innerHTML = "";
            pagesEl.appendChild(frag);
            host.classList.remove("is-loading");
            host.removeAttribute("aria-busy");
        }

        await renderAll();
        if (typeof ResizeObserver !== "undefined") {
            var ro = new ResizeObserver(debounce(renderAll, 120));
            ro.observe(host);
        } else {
            window.addEventListener("resize", debounce(renderAll, 120));
        }
    }

    async function mountHtml(host, url) {
        if (host.dataset.ready === "1") return;
        host.dataset.ready = "1";
        host.classList.add("is-loading");
        host.setAttribute("aria-busy", "true");

        var res = await fetch(url, { credentials: "same-origin" });
        if (!res.ok) throw new Error("HTTP " + res.status);
        var text = await res.text();
        var doc = new DOMParser().parseFromString(text, "text/html");
        var sheet = document.createElement("article");
        sheet.className = "documents-html-sheet";
        sheet.innerHTML = doc.body ? doc.body.innerHTML : text;
        host.innerHTML = "";
        host.appendChild(sheet);
        host.classList.remove("is-loading");
        host.removeAttribute("aria-busy");
    }

    function mount(host) {
        if (!host || host.dataset.ready === "1") return;
        var kind = host.getAttribute("data-doc-viewer");
        var url = host.getAttribute("data-src");
        if (!url) return;
        var run = kind === "html" ? mountHtml(host, url) : mountPdf(host, url);
        run.catch(function (err) {
            host.dataset.ready = "0";
            host.classList.remove("is-loading");
            host.innerHTML =
                '<p class="documents-viewer-error">Не удалось открыть документ. ' +
                '<a href="' +
                url +
                '" target="_blank" rel="noopener">Открыть отдельно</a>.</p>';
            console.error("[documents-viewer]", err);
        });
    }

    function mountVisible(root) {
        if (!root) return;
        root.querySelectorAll("[data-doc-viewer]").forEach(function (host) {
            var panel = host.closest("[hidden], .documents-panel");
            if (panel && panel.hasAttribute("hidden")) return;
            mount(host);
        });
    }

    window.ryptDocumentsViewer = {
        mount: mount,
        mountVisible: mountVisible,
    };

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("[data-documents-tabs]").forEach(function (root) {
            mountVisible(root);
        });
    });
})();

# PdfCraft Web on GitHub Pages

This repository builds the official open-source [PdfCraft](https://github.com/storytold/pdfcraft) WebAssembly app and publishes the static web build to GitHub Pages.

Upstream source: https://github.com/storytold/pdfcraft

Current pinned upstream release: **v0.10.1**

The web build uses relative asset URLs, so it can run from the existing GitHub Pages project path:

`https://appbuilderlee2.github.io/printcraft-web/`

The repository name and Pages URL remain `printcraft-web` for compatibility with existing bookmarks and the installed PWA, while the app itself now builds PdfCraft v0.10.1.

## Licensing

PdfCraft source is licensed under the licenses provided by the upstream project. This wrapper repository does not claim ownership of PdfCraft. See the upstream repository for license, notice, attribution, and trademark terms.

## PDF translation companion

The deployment now also publishes [PDF Translator](https://appbuilderlee2.github.io/printcraft-web/translator/) with three features:

1. Select PDF text and translate it to another language.
2. Read the extracted original text alongside translated text, one page at a time.
3. Translate every text page and use Print / Save as PDF to export a translated or bilingual document.

The translator uses PDF.js to extract text locally. Translation requests send extracted text to the third-party MyMemory translation API and require an internet connection; therefore avoid confidential files. There are translation rate/size limits. Image-only PDFs need OCR first. Export reconstructs text and does not preserve complex original layout. It is a companion page and does not modify the upstream PdfCraft app.

The translation tool is copied into the Pages output before the PWA cache is generated. Its JavaScript and PDF.js dependency load in the browser. Live browser compatibility has not yet been independently verified.

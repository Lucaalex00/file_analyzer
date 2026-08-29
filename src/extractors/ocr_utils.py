import pytesseract


def preprocess_for_ocr(image):
    # Table borders, background shading, and JPEG compression artifacts can
    # all be misread by Tesseract as stray characters -- a plain grayscale
    # threshold removes faint lines/noise while keeping solid text.
    grayscale = image.convert("L")
    return grayscale.point(lambda pixel: 255 if pixel > 150 else 0)


def mean_ocr_confidence(image, lang="ita"):
    # Tesseract reports a 0-100 confidence per recognized word (-1 for
    # regions it didn't treat as a word at all). Averaging only over words
    # it actually produced text for is a cheap signal for "does this image
    # contain real, reliably readable text" versus a logo or decorative
    # graphic where Tesseract hallucinates a character or two from shapes.
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
    confidences = [int(conf) for conf, text in zip(data["conf"], data["text"]) if text.strip() and int(conf) >= 0]
    if not confidences:
        return 0.0
    return sum(confidences) / len(confidences)

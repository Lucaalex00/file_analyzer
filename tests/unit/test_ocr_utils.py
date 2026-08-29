from PIL import Image, ImageDraw, ImageFont

from src.extractors.ocr_utils import mean_ocr_confidence, preprocess_for_ocr


def _render_text_image(text: str) -> Image.Image:
    image = Image.new("RGB", (600, 150), color="white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=40)
    draw.text((10, 40), text, fill="black", font=font)
    return image


class TestPreprocessForOcr:
    def test_converts_to_grayscale_and_thresholds_to_pure_black_and_white(self):
        image = Image.new("RGB", (2, 1))
        image.putpixel((0, 0), (200, 200, 200))  # above threshold -> white
        image.putpixel((1, 0), (50, 50, 50))  # below threshold -> black

        result = preprocess_for_ocr(image)

        assert result.mode == "L"
        assert result.getpixel((0, 0)) == 255
        assert result.getpixel((1, 0)) == 0


class TestMeanOcrConfidence:
    def test_returns_a_high_confidence_for_clear_rendered_text(self):
        image = _render_text_image("HELLO WORLD")

        assert mean_ocr_confidence(image) > 50

    def test_returns_zero_when_no_words_are_recognized(self):
        # Pure geometric shapes -- like a vector logo -- with no real text
        # at all: Tesseract recognizes no words, so there's nothing to
        # average and the signal should default to "not confident".
        image = Image.new("RGB", (300, 300), color="white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((50, 50, 250, 250), outline="black", width=8)
        draw.line((50, 150, 250, 150), fill="black", width=4)

        assert mean_ocr_confidence(image) == 0.0

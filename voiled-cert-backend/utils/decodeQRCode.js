const jimp = require("jimp");
const jsQR = require("jsqr");

const decodeQRCode = async (imagePath) => {
    try {
        const image = await jimp.read(imagePath);
        const imageData = {
            data: new Uint8ClampedArray(image.bitmap.data),
            width: image.bitmap.width,
            height: image.bitmap.height,
        };

        const decodedQR = jsQR(imageData.data, imageData.width, imageData.height);

        if (decodedQR) {
            return decodedQR.data;
        } else {
            throw new Error("QR code not found in the image.");
        }
    } catch (error) {
        console.error("Error decoding QR code:", error);
    }
}

export default decodeQRCode;
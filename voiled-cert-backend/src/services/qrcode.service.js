const httpStatus = require('http-status');
const config = require('../config/config');
const ApiError = require('../utils/ApiError');

const { Jimp } = require("jimp");
const jsQR = require("jsqr");

const decodeQRCode = async (imagePath) => {
    // try {
        const image = await Jimp.read(imagePath);

        const imageData = {
            data: new Uint8ClampedArray(image.bitmap.data),
            width: image.bitmap.width,
            height: image.bitmap.height,
        };

        

        const decodedQR = jsQR(imageData.data, imageData.width, imageData.height);

        if (decodedQR) {
            return decodedQR.data;
        }
        // else {
        //     throw new ApiError("QR code not found in the image.");
        // }
//     } catch (error) {
//         throw new ApiError("QR code not found in the image.");
//     }
}

module.exports = {
    decodeQRCode
}
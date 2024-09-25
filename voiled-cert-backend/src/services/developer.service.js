const httpStatus = require('http-status');
const { Developer, User } = require('../models');
const ApiError = require('../utils/ApiError');
const { generateVerifyCertificateToken } = require('./token.service');
const { getUserById } = require("./user.service");
const { sendEmail } = require('./email.service');
const { tokenService } = require('.');
const { tokenTypes } = require('../config/tokens');

/**
 * @param {String} userId 
 */
const getDeveloperByUserId = async (userId) => {
    return Developer.findOne({ user: userId }).populate("user", "name email");
}

/**
 * @param {String} userId
 * @param {Object} developerBody
 */
const upsertDeveloperByUserId = async (upsertBody) => {
    try {
        const developer = await Developer.findOne({ user: upsertBody.user });
    
        if (!developer) {
            await Developer.create(upsertBody);
        } else {
            Object.assign(developer, upsertBody);
            await developer.save();
        }
        return developer;
    } catch (error) {
        console.log(error);
        
        throw new ApiError(httpStatus.extra, 'Some error'); 
    }
}

const sendVerifyCodeToOwner = async (ownerId, receiverId) => {
    try {
        let verifyToken = await generateVerifyCertificateToken(ownerId, receiverId);

        let owner = await getUserById(ownerId);

        console.log(">>>>>>>>>>>>>>>>", owner);
        

        let html = `
            <h1>${verifyToken}</h1>
            <p>Click below button to go to verify page and input your verify code. </p>
            <a href='http://localhost:3000/verify/${receiverId}'>
                <button style="cursor: pointer; border: none; background-color: red; color: white; padding: 10px 20px; text-decoration: none; border-radius: 10px;">Click Me</div>
            </a>
        `
        sendEmail(owner.email, "Check verify code for your certificate.", `This is verify code.`, html);
    } catch (err) {
        console.log(err);
        throw new ApiError(httpStatus.extra, 'Some error'); 
    }
}

const verifyCertWithToken = async (ownerId, token) => {
    try {
        let tokenToc = await tokenService.verifyCertificateToken(token, tokenTypes.VERIFY_CERTIFICATE, ownerId);

        if (tokenToc) {
            let receiver = await getUserById(tokenToc.receiver);

            let html = `
                <h1>Hi, ${receiver.name}</h1>
                <h2>He/She is the owner of certificate. You can trust him/her. Best regards.</h2>
            `

            console.log(receiver);
            

            sendEmail(receiver.email, "Notification from Voiled.", '', html);
            return true;
        } else {
            return false;
        }
    } catch (error) {
        console.log(error);
        return false;
        
    }
}

module.exports = {
    getDeveloperByUserId,
    upsertDeveloperByUserId,
    sendVerifyCodeToOwner,
    verifyCertWithToken
}
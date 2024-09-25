const httpStatus = require('http-status');
const { Developer, User } = require('../models');
const ApiError = require('../utils/ApiError');
const { generateVerifyCertificateToken } = require('./token.service');
const { getUserById } = require("./user.service");
const { sendEmail } = require('./email.service');

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

module.exports = {
    getDeveloperByUserId,
    upsertDeveloperByUserId,
    sendVerifyCodeToOwner
}
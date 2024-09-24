const httpStatus = require('http-status');
const { Developer } = require('../models');
const ApiError = require('../utils/ApiError');

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

module.exports = {
    getDeveloperByUserId,
    upsertDeveloperByUserId
}
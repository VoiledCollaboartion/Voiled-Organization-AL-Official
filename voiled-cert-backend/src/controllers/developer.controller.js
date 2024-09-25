const httpStatus = require('http-status');
const pick = require('../utils/pick');
const ApiError = require('../utils/ApiError');
const catchAsync = require('../utils/catchAsync');
const { developerService } = require('../services');

const upsertDeveloper = catchAsync(async (req, res) => {
    const developer = await developerService.upsertDeveloperByUserId(req.body);
    res.status(httpStatus.CREATED).send(developer);
});

const getDeveloper = catchAsync(async (req, res) => {
    const developer = await developerService.getDeveloperByUserId(req.params.userId);
    if (!developer) {
        throw new ApiError(httpStatus.NOT_FOUND, 'User not found');
    }
    res.send(developer);
})

const verifyCertOwner = catchAsync(async (req, res) => {
    const { receiverId, ownerId } = pick(req.body, ['ownerId', 'receiverId']);
    await developerService.sendVerifyCodeToOwner(ownerId, receiverId);
    res.send("success");
});

const verifyCertOwnerFinallyWithToken = catchAsync(async (req, res) => {
    const { ownerId } = pick(req.query, ['ownerId']);
    const { token } = pick(req.body, ['token']);

    await developerService.verifyCertWithToken(ownerId, token);

    return res.send("success");
})

module.exports = {
    upsertDeveloper,
    getDeveloper,
    verifyCertOwner,
    verifyCertOwnerFinallyWithToken
}
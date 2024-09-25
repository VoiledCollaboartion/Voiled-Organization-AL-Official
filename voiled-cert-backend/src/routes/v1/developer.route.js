const express = require('express');
const developerController = require('../../controllers/developer.controller');
const auth = require('../../middlewares/auth');

const router = express.Router();

router.post('/upsert', auth(), developerController.upsertDeveloper);
router.get("/:userId", auth(), developerController.getDeveloper);
router.post('/verify/send', developerController.verifyCertOwner);
router.post("/verify/compare", developerController.verifyCertOwnerFinallyWithToken);

module.exports = router;
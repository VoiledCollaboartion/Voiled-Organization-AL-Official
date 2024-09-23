import { Router }       from "express";
import * as userCtr     from "../controllers/user";

const userRouter = Router();

userRouter.get("/test", (req, res) => {
    return res.send("user router test ok");
})

userRouter.post("/register",     userCtr.registerFreelancer);
userRouter.post("/genQRCode",    userCtr.generateQRCode);
userRouter.post("/verifyQRCode", userCtr.verifyWithQRCode);

export default userRouter;
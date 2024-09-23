import dotenv      from "dotenv";
import initExpress from "./config/express";
import connectDB   from "./config/mongoose";

dotenv.config();

connectDB();
const app = initExpress();

const port = process.env.PORT || 8081;

app.listen(port, () => {
    console.log(`Server Started at port ${port}`);
});
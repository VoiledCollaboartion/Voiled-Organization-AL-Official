import express      from "express";
import cors         from "cors"
import bodyParser   from "body-parser";
import morgan       from "morgan";
import compression from "compression";

import router       from "../routes";

const initExpress = () => {
    const app = express();

    app.use(cors());
    app.use(bodyParser.json());
    app.use(bodyParser.urlencoded({ extended: false }));

    const ENV = process.env.NODE_ENV || "dev"

    if (ENV === "dev") {
        app.use(morgan("dev"));
    } else {
        app.use(compression());
    }

    app.use("/", router);

    return app;
}

export default initExpress;
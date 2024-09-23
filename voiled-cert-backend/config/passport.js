import { Strategy as JwtStrategy, ExtractJwt } from 'passport-jwt';
import key                                     from './key';
import User                                    from '../models/user';

const ENV = process.env.NODE_ENV || "dev";

let opts = {};

opts.jwtFromRequest = ExtractJwt.fromAuthHeaderAsBearerToken();
opts.secretOrKey    = key[ENV].secretOrKey;

passport.use(new JwtStrategy(opts, function (jwt_payload, done) {
    User.findOne({ id: jwt_payload.sub }, function (err, user) {
        if (err) {
            return done(err, false);
        }
        if (user) {
            return done(null, user);
        } else {
            return done(null, false);
            // or you could create a new account
        }
    });
}));
export const STATUS_MESSAGE = {
    405: "Server Error",
    406: "Other Error",
    200: "Request success"
}

const makeResponse = (status, data, msg) => {
    return {
        success: status === 200,
        msg    : msg || STATUS_MESSAGE[status],
        data   : data
    }
}

export default makeResponse;
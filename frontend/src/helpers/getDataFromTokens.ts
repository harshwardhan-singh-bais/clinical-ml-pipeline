import { NextRequest } from "next/server";
import Jwt from "jsonwebtoken";

export async function getDataFromTokens(request: NextRequest) {
    try {
        const token = request.cookies.get("token")?.value || "";
        const decodedToken:any = Jwt.verify(token, process.env.JWT_SECRET_KEY!)
        return decodedToken.id;
    } catch (error: any) {
        console.log("Get data from token error", error.message);
    }
}
import { connect } from "@/dbConfig/dbConfig";
import User from "@/models/userModel"
import { NextResponse, NextRequest } from "next/server";
import bcryptjs from "bcryptjs";
import jwt from "jsonwebtoken"

connect()

export async function POST(request: NextRequest) {
    try {
        const reqBody = await request.json()
        const { email, password } = reqBody
        console.log(reqBody)

        //Check if User exists
        const user = await User.findOne({ email })
        if (!user) {
            return NextResponse.json({ message: "User does not exist" }, { status: 400 });
        }

        //check if password is correct
        const validPassword = await bcryptjs.compare(password, user.password);
        if (!validPassword) {
            return NextResponse.json({ message: "Invalid password" }, { status: 400 });
        }

        //create token data
        const tokenData = {
            id: user._id,
            username: user.username,
            email: user.email
        }

        // Ensure secret exists
        if (!process.env.JWT_SECRET_KEY) {
            throw new Error("TOKEN_SECRET is not defined in environment variables");
        }

        // create token
        const token = await jwt.sign(tokenData,
            process.env.JWT_SECRET_KEY!,
            {expiresIn: "1d"}
        )

        const response = NextResponse.json({
            message: "Login successful",
            success: true
        })

        response.cookies.set("token", token, {
            httpOnly: true,
        })

        return response;
    } catch (error: any) {
        console.log("Login error:", error.message);
        return NextResponse.json({message: error.message}, {status: 500});
    }
}
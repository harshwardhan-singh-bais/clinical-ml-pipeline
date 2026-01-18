import {connect} from "@/dbConfig/dbConfig"
import { NextResponse, NextRequest } from "next/server"
import User from "@/models/userModel"

connect()

export async function POST(request: NextRequest) {
    try {
        const reqBody = await request.json()
        const { token } = reqBody
        console.log("Token received", token)

        const user = await User.findOne({
            verifyToken: token,
            verifyTokenExpiry: { $gt: Date.now() }
        })

        if (!user)
            return NextResponse.json({
                message: "Invalid or expired token",
                success: false
            }, { status: 400 })

        console.log(user)

        user.isVerified = true
        user.verifyToken = undefined
        user.verifyTokenExpiry = undefined
        await user.save()

        return NextResponse.json({
            message: "Email verified successfully",
            success: true
        }, { status: 200 })
    } catch (error) {
        console.log("Error in verifying email", error)
        return NextResponse.json({message: "Internal Server Error", success: false}, {status: 500})
    }
}
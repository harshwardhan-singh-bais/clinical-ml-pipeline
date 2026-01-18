import { getDataFromTokens } from "@/helpers/getDataFromTokens";
import { NextResponse, NextRequest } from "next/server";
import { connect } from "@/dbConfig/dbConfig"
import User from "@/models/userModel";

connect();

export async function GET(request: NextRequest) {
    try {
        const userId = await getDataFromTokens(request);
        const user = await User.findOne({ _id: userId }).select("-password");
        
        return NextResponse.json({
            message: "User data fetched successfully",
            data: user
        });
    } catch (error: any) {
        return NextResponse.json({message: "Error fetching user data: " + error.message}, {status: 500});            
    }
}
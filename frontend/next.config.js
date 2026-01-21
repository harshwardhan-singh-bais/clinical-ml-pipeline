/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // Suppress hydration warnings and expected errors
    onDemandEntries: {
        maxInactiveAge: 25 * 1000,
        pagesBufferLength: 2,
    },
    // Don't show error overlay for expected validation errors
    compiler: {
        removeConsole: process.env.NODE_ENV === 'production' ? {
            exclude: ['error', 'warn'],
        } : false,
    },
}

module.exports = nextConfig

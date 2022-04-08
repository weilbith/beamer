/* eslint-disable no-console */
async function main() {
    console.log("Hello");
}

main().catch((err) => {
    console.error('Main error:', err);
    process.exit(2);
});

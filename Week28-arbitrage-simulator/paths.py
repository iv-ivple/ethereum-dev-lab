# paths.py

WETH  = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC  = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
DAI   = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
USDT  = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
WBTC  = "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"

# Format: list of {"pair": pair_address, "token_in": address_of_input_token_for_this_hop}
TRIANGLES = [
    {
        "name": "WETH→USDC→DAI→WETH",
        "start_token": WETH,
        "path": [
            {"pair": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "token_in": WETH},  # WETH/USDC Uni V2
            {"pair": "0xAE461cA67B15dc8dc81CE7615e0320dA1A9aB8D5", "token_in": USDC},  # USDC/DAI  Uni V2
            {"pair": "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11", "token_in": DAI},   # DAI/WETH  Uni V2
        ]
    },
    {
        "name": "WETH→USDT→DAI→WETH",
        "start_token": WETH,
        "path": [
            {"pair": "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852", "token_in": WETH},  # WETH/USDT Uni V2
            {"pair": "0xB20bd5D04BE54f870D5C0d3cA85d82b34B836405", "token_in": USDT},  # USDT/DAI  Uni V2
            {"pair": "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11", "token_in": DAI},   # DAI/WETH  Uni V2
        ]
    },
    {
        "name": "WETH→USDC→USDT→WETH",
        "start_token": WETH,
        "path": [
            {"pair": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "token_in": WETH},  # WETH/USDC Uni V2
            {"pair": "0x3041CbD36888bECc7bbCBc0045E3B1f144466f5f", "token_in": USDC},  # USDC/USDT Uni V2
            {"pair": "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852", "token_in": USDT},  # USDT/WETH Uni V2
        ]
    },
    {
        "name": "WETH→WBTC→USDC→WETH",
        "start_token": WETH,
        "path": [
            {"pair": "0xBb2b8038a1640196FbE3e38816F3e67Cba72D940", "token_in": WETH},  # WETH/WBTC Uni V2
            {"pair": "0x004375Dff511095CC5A197A54140a24eFEF3A416", "token_in": WBTC},  # WBTC/USDC Uni V2
            {"pair": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "token_in": USDC},  # USDC/WETH Uni V2
        ]
    },
    {
        "name": "WETH→WBTC→DAI→WETH",
        "start_token": WETH,
        "path": [
            {"pair": "0xBb2b8038a1640196FbE3e38816F3e67Cba72D940", "token_in": WETH},  # WETH/WBTC Uni V2
            {"pair": "0x231B7589426Ffe1b75405526fC32aC09D44364c4", "token_in": WBTC},  # WBTC/DAI  Uni V2
            {"pair": "0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11", "token_in": DAI},   # DAI/WETH  Uni V2
        ]
    },
]

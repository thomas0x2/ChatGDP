import etl

BASE_TICKER = ["NESN.SW", "ROG.SW", "NOVN.SW", "CFR.SW", "ZURN.SW", "UBSG.SW", "PGHN.SW", "SREN.SW", "SLHN.SW"]
BASE_PEERS = {
            "NESN.SW": ["BN.PA", "ULVR.L", "PEP", "MDLZ", "KHC"],
            "ROG.SW": ["NOVN.SW", "PFE", "LLY", "NOVO-B.CO", "JNJ"],
            "NOVN.SW": ["ROG.SW", "PFE", "LLY", "NOVO-B.CO", "JNJ"],
            "CFR.SW": ["MC.PA", "UHR.SW", "KER.PA", "RMS.PA"],
            "ZURN.SW": ["ALV.DE", "CS.PA", "G.MI"],
            "UBSG.SW": ["MS", "JPM", "BAC", "BNP.PA", "DBK.DE"],
            "PGHN.SW": ["BX", "APO", "KKR", "CG", "EQT.ST", "CVC.AS"],
            "SREN.SW": ["MUV2.DE", "HNR1.DE", "SCR.PA"],
            "SLHN.SW": ["LGEN.L", "PRU.L", "AGN.AS", "NN.AS"]
            }

for ticker in BASE_TICKER:
    etl.load_data(ticker)
    etl.load_peers(ticker, BASE_PEERS[ticker])
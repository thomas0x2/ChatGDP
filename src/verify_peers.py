import etl
import metrics
import pandas as pd

def test_peer_retrieval():
    ticker = "UBSG.SW"
    peers = etl.transform_peers(ticker)
    print(f"Peers for {ticker}: {peers}")
    assert isinstance(peers, list)
    assert len(peers) > 0
    assert "MS" in peers

def test_peer_metrics():
    ticker = "UBSG.SW"
    peers = etl.transform_peers(ticker)
    comparison_tickers = [ticker] + peers
    
    for t in comparison_tickers:
        pe = metrics.calculate_pe(t)
        pb = metrics.calculate_pb(t)
        print(f"{t} - PE: {pe.iloc[0] if not pe.empty else 'N/A'}, PB: {pb.iloc[0] if not pb.empty else 'N/A'}")

if __name__ == "__main__":
    print("Testing peer retrieval...")
    test_peer_retrieval()
    print("\nTesting peer metrics...")
    test_peer_metrics()
    print("\nVerification complete.")

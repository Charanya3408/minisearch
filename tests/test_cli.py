from minisearch.cli import main


def test_cli_finds_sample_document(capsys):
    assert main(["inverted", "index"]) == 0
    assert "Inverted index" in capsys.readouterr().out


def test_cli_reports_no_results(capsys):
    main(["zzzzqqqq"])
    assert "No results." in capsys.readouterr().out

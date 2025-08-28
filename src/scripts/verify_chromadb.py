import sys

try:
	import chromadb
except Exception as exc:
	print("Failed to import chromadb:", exc)
	sys.exit(1)


def main() -> None:
	try:
		client = chromadb.Client()
		collections = client.list_collections()
		print("ChromaDB reachable. Collections:", collections)
	except Exception as exc:
		print("ChromaDB client error:", exc)
		sys.exit(2)


if __name__ == "__main__":
	main()




from isuvalidation import check_credentials

# result = check_credentials("yannick", "password")
result = check_credentials("yannick.matimbe", "M@timbeAndFenix@13102025")

print(result)
if result["success"]:
    print("Credentials are valid.")
else:
    print(f"Login failed: {result['code']} - {result['message']}")
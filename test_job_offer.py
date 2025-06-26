from app import analyze_message

message = """Subject: Job Opportunity at Infosys – Software Engineer Role

Hello Aman,

We came across your profile and wanted to reach out regarding an open Software Engineer position at Infosys.

Job Location: Pune (Hybrid)
Salary: ₹7.2 LPA
Experience Required: 1–3 years
Skills Needed: Java, Spring Boot, REST APIs

The hiring process includes:

Online coding test
Two rounds of technical interviews
One HR discussion

No fees are involved at any stage of the recruitment process. Interviews will be scheduled via Microsoft Teams or Google Meet.

To apply, visit our official career page:
https://www.infosys.com/careers

Best regards,
Ritika Sharma
Recruitment Team – Infosys
hr@infosys.com"""

print("Testing improved scam detection system...")
print("=" * 50)

result = analyze_message(message)
print(f"Verdict: {result['verdict']}")
print(f"Summary: {result['summary']}")
print(f"Evidence: {result['evidence']}")
print(f"Source: {result['source']}")

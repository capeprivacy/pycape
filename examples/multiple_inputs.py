from pycape.cape import Cape
import asyncio

async def run():

    cape = Cape(token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlBVMlpQR0d6a3gzbEQzX0JnOUdiRSJ9.eyJpc3MiOiJodHRwczovL21hZXN0cm8tZGV2LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExNzUyNjQ3NDY4MTA5ODA2NDMyMyIsImF1ZCI6WyJodHRwczovL25ld2RlbW8uY2FwZXByaXZhY3kuY29tL3YxLyIsImh0dHBzOi8vbWFlc3Ryby1kZXYudXMuYXV0aDAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTY1NTE3NzUyOSwiZXhwIjoxNjU1MjYzOTI5LCJhenAiOiJ5UW5vYmtPcjFwdmREQXlYd05vamtOVjJJUGJOZlh4eCIsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwifQ.PTVOqxY9EjSaU1FhdcsCMIZpHEv0ouMpw7aN631hXjdRctFfi-7uLhpFOT1E_ZuQHt7U9RmposbVME0Yq_6fyv14Rk4nBtNNRvl-1x28IuETV-6Ix5YHjo1X1oEnMWJ2_X-m8P_82dvxVWHmeAt9Qigt0KK0Y62_P-i6DrJMxbGOJzvF4_3tVOP65CFhCrPphnDik3q7L9RTdmjI7uatgRbAJiINJE4zAjuF6bzOPhYPOdW6SOJXuGrOu0ZyXtQW4bHEpyNJZQ2OpeTP2jm6PPoHXK5xjftKddFOgIoNKjjXQ6c9KKxczkhi1tgoXN_DD3z9JuplAZUYO4tf9j97Uw")

    await cape.connect("e4c2a674-9c7f-42d3-8ade-63791c16c3c7")

    result = await cape.invoke('Hello Cape')
    print(f"The result is: {result}")

    result = await cape.invoke('Hello Gavin')
    print(f"The result is: {result}")

    result = await cape.invoke('Hello Hello')
    print(f"The result is: {result}")

    await cape.close()

if __name__ == "__main__":
    asyncio.run(run())

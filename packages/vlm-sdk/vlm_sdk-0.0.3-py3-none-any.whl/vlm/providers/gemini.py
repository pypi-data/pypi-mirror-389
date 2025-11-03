import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
from google import genai
from google.genai import types
from .base import BaseVideoProvider

MODEL = "gemini-2.5-flash"


class GeminiVideoService(BaseVideoProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required")

        self.client = genai.Client(api_key=api_key)

        self.config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            candidate_count=1,
            max_output_tokens=2048,
        )

    async def upload_file(self, file_path: Path) -> Dict[str, Any]:
        """Upload a file to Gemini Files API following the documentation pattern"""
        try:
            # Upload file to Gemini using the same pattern as the documentation
            uploaded_file = await self.client.aio.files.upload(file=file_path)

            # Wait for file to be processed
            while uploaded_file.state == "PROCESSING":
                await asyncio.sleep(1)
                uploaded_file = await self.client.aio.files.get(name=uploaded_file.name)

            if uploaded_file.state == "FAILED":
                raise Exception(f"File upload failed: {uploaded_file.error}")

            return {
                "name": uploaded_file.name,
                "uri": uploaded_file.uri,
                "mime_type": uploaded_file.mime_type,
                "size_bytes": uploaded_file.size_bytes,
                "state": uploaded_file.state,
                "display_name": uploaded_file.display_name,
                "create_time": uploaded_file.create_time.isoformat()
                if uploaded_file.create_time
                else None,
                "update_time": uploaded_file.update_time.isoformat()
                if uploaded_file.update_time
                else None,
                "file_object": uploaded_file,  # Store the actual file object for later use
            }

        except Exception as e:
            raise Exception(f"Failed to upload file to Gemini: {str(e)}")


    async def delete_file(self, file_uri: str) -> bool:
        """Delete a file from Gemini"""
        try:
            await self.client.aio.files.delete(name=file_uri)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")


    async def query_video_with_file(self, file_uri: str, prompt: str) -> str:
        """Query a video using its Gemini file URI, following documentation pattern"""
        try:
            # Get the file object
            file = await self.client.aio.files.get(name=file_uri)

            # Generate content using the same pattern as the documentation
            response = await self.client.aio.models.generate_content(
                model=MODEL,
                contents=[
                    file,
                    "\n\n",
                    prompt,
                ],
            )

            return response.text

        except Exception as e:
            return f"Error processing video: {str(e)}"

    async def find_timestamp_with_file(
        self, file_uri: str, query: str
    ) -> Dict[str, Any]:
        """Find a timestamp in video using its Gemini file URI"""
        try:
            # Get the file object
            file = await self.client.aio.files.get(name=file_uri)

            prompt = f"""Analyze this video and find the timestamp that best matches the following query: {query}

Return ONLY a JSON object with these fields:
- timestamp: the time in seconds (number)
- confidence: confidence score between 0 and 1 (number)
- description: brief description of what happens at that timestamp (string)

Example response:
{{"timestamp": 45.5, "confidence": 0.85, "description": "Person waves at the camera"}}"""

            # Generate content using the same pattern as the documentation
            response = await self.client.aio.models.generate_content(
                model=MODEL,
                contents=[
                    file,
                    "\n\n",
                    prompt,
                ],
            )

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                return {
                    "timestamp": 0,
                    "confidence": 0,
                    "description": response_text,
                }

        except Exception as e:
            return {"error": str(e)}

    async def find_multiple_timestamps_with_file(
        self, file_uri: str, query: str
    ) -> Dict[str, Any]:
        """Find multiple timestamps in video that match the query"""
        try:
            # Get the file object
            file = await self.client.aio.files.get(name=file_uri)

            prompt = f"""Analyze this video and find ALL timestamps that match the following query: {query}

Return ONLY a JSON object with these fields:
- timestamps: an array of matching timestamps, where each item has:
  - timestamp: the time in seconds (number)
  - confidence: confidence score between 0 and 1 (number)
  - description: brief description of what happens at that timestamp (string)
- total_found: the total number of matching timestamps found (number)

Example response:
{{
  "timestamps": [
    {{"timestamp": 12.5, "confidence": 0.95, "description": "First occurrence of person waving"}},
    {{"timestamp": 45.5, "confidence": 0.85, "description": "Person waves again at the camera"}},
    {{"timestamp": 78.0, "confidence": 0.75, "description": "Brief wave before leaving"}}
  ],
  "total_found": 3
}}

If only one match is found, still return it in an array format.
If no matches are found, return an empty timestamps array with total_found: 0."""

            # Generate content using the same pattern as the documentation
            response = await self.client.aio.models.generate_content(
                model=MODEL,
                contents=[
                    file,
                    "\n\n",
                    prompt,
                ],
            )

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            try:
                result = json.loads(response_text)
                # Ensure the response has the expected structure
                if "timestamps" not in result:
                    result = {"timestamps": [], "total_found": 0}
                if "total_found" not in result:
                    result["total_found"] = len(result.get("timestamps", []))
                return result
            except json.JSONDecodeError:
                return {
                    "timestamps": [],
                    "total_found": 0,
                    "error": "Failed to parse response",
                    "raw_response": response_text,
                }

        except Exception as e:
            return {"error": str(e), "timestamps": [], "total_found": 0}


    async def analyze_video_range(
        self, file_uri: str, start_time: str, end_time: str, prompt: str
    ) -> str:
        """Analyze a video between two timestamps"""
        try:
            # Get the file object
            file = await self.client.aio.files.get(name=file_uri)

            # Create the prompt for range analysis
            formatted_prompt = f"""Please analyze this video between {start_time} and {end_time}.

{prompt}

Focus specifically on what happens during this time period from {start_time} to {end_time}."""

            # Generate content using the same pattern as the documentation
            response = await self.client.aio.models.generate_content(
                model=MODEL,
                contents=[
                    file,
                    "\n\n",
                    formatted_prompt,
                ],
            )

            return response.text

        except Exception as e:
            return f"Error analyzing video range: {str(e)}"





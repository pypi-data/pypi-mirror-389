import json
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from typing import Any, List, Optional
from pydantic import BaseModel

getcontext().prec = 7
getcontext().rounding = ROUND_HALF_EVEN

class AWSAlternative(BaseModel):
    confidence: str
    content: str

class AWSItem(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    alternatives: List[AWSAlternative]
    type: str

class AWSTranscript(BaseModel):
    transcript: str

class AWSResults(BaseModel):
    transcripts: List[AWSTranscript]
    items: List[AWSItem]

class AWSSchema(BaseModel):
    results: AWSResults

class DGWord(BaseModel):
    word: str
    start: float
    end: float
    confidence: float

class DGAlternative(BaseModel):
    transcript: str
    confidence: float
    words: List[DGWord]

class DGChannel(BaseModel):
    alternatives: List[DGAlternative]

class DGResults(BaseModel):
    channels: List[DGChannel]

class DGSchema(BaseModel):
    results: DGResults

def normalize_schema(aws_data: dict[str, Any]) -> dict[str, Any]:
    """
        Converts from the AWS Transcribe JSON schema to the Deepgram JSON schema
    """
    # Validate input with pydantic
    aws_obj = AWSSchema(**aws_data)

    total_confidence = 0
    words = []

    for item in aws_obj.results.items:
        if item.type != 'pronunciation':  # Skips over punctuation items, which are not present in Deepgram outputs
            continue

        confidence = float(Decimal(item.alternatives[0].confidence))
        total_confidence += confidence
        words.append(DGWord(
            word=item.alternatives[0].content,
            start=float(Decimal(item.start_time)),
            end=float(Decimal(item.end_time)),
            confidence=confidence,
        ))

    avg_confidence = 0.0
    if words:
        avg_confidence = total_confidence / len(words)

    dg_schema = DGSchema(
        results=DGResults(
            channels=[
                DGChannel(
                    alternatives=[
                        DGAlternative(
                            transcript=aws_obj.results.transcripts[0].transcript,
                            confidence=float(Decimal(str(avg_confidence))),
                            words=words
                        )
                    ]
                )
            ]
        )
    )

    return dg_schema.model_dump()

def lambda_handler(event, context):
    try:
        return {
            'statusCode': 200,
            'body': json.dumps(normalize_schema(event))
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
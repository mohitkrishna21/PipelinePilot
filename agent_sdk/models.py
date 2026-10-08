from pydantic import BaseModel, Field
from typing import Literal

class JDBreakdown(BaseModel):
    company: str = Field(description="The hiring company's name exactly as written in the job description. Use 'Not stated' if it is missing.")
    role : str = Field(description="The job title exactly as written, for example 'Applied AI Engineer'. Use 'Not stated' if there is no title.")
    must_have_skills: list[str] = Field(description="Skills, tools or experience the posting says are required, using words like 'required', 'must have' or 'you will need'. Use short names only, such as 'Python', not 'strong Python experience'.")
    nice_to_have_skills: list[str] = Field(description="Skills marked as preferred, a bonus, a plus, or 'nice to have'. Do not repeat anything already in must_have_skills.")
    red_flags: list[str] = Field(description="Warning signs for a junior candidate: too many years of experience required, on-call, unpaid work, vague pay, an unrealistic list of tools. Return an empty list if there are none. Do not invent flags.")
    work_authorization_quote: str = Field(description="The exact sentence or phrase from the posting about citizenship, work authorization, visa sponsorship, security clearance or export control. Use 'Not stated' if the posting says nothing about it.")
    work_authorization: Literal["citizens_or_us_persons_only", "no_sponsorship", "sponsorship_offered", "not_stated"] = Field(description="Classify the language in the quote. 'citizens_or_us_persons_only' means US citizens, US persons, a security clearance or export-control (ITAR) rules; 'no_sponsorship' means candidates must be authorized to work without current or future sponsorship; 'sponsorship_offered' means the company says it sponsors visas; 'not_stated' means no such language. Use only what the posting says; never guess from the company name.")




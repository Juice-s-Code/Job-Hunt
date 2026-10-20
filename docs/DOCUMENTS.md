# Evidence, tailoring and document release

## Establish the evidence bank

The candidate supplies their own resume and source documents. Keep immutable
originals privately; never edit a transcript. For every usable claim record its
wording, source/locator, exact dates, task/tool, scale, ownership, outcome, approval
and limits. `templates/EVIDENCE.md` supplies a blank format. Ask about experience
missing from the resume; an owner's claim that there is more work is a prompt to
elicit details, not permission to invent them. Conflicts remain unresolved.

No generated graph, previous assistant assertion, synthetic fixture or another
candidate's document is evidence. A dollar figure, GPA, title, skill or honor must
have an approved basis. Distinguish participating, supporting and owning work.

## Draft the packet

Read the full posting and approved evidence. Select the most relevant truthful
experiences, emphasize transferable work, and retain correct employers, titles,
dates and proficiency levels. Use concrete task/action/result wording. Do not
insert job-description keywords that imply experience the candidate lacks.

Use a simple structure with conventional headings and readable chronology. Match
the employer's required file format. A one-page early-career resume may be useful;
the owner's background and employer instructions determine the actual length.
Avoid decorative layouts that break text extraction. Do not pretend these prose
rules are an automated ATS certification.

Write a cover letter when accepted and useful, grounded in the role brief and
approved experience. Keep it a draft until the owner reviews factual content and
voice and releases it. Applicant AI restrictions and authorship attestations can
require the owner to write content independently; stop rather than paraphrasing
around the restriction. Do not generate assessment or interview responses where
the employer forbids assistance.

## Release actual bytes

Use `templates/PACKET-MANIFEST.md` privately. Record exact job identity and each
file's absolute path, SHA-256, type, review time, evidence approval, rendering and
release status. Hash the actual file, not an earlier version:

```text
python -B -c "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" "ACTUAL_FILE"
```

Open the rendered document, check page count, clipping, headings, dates, bullet
readability and contact details. Extract text with an available approved tool and
compare it with the visual output. Confirm no comments, tracked changes, hidden
draft text or placeholder fields remain. The bundled core neither renders DOCX/PDF
nor verifies their semantic content; document tools require separate setup.

Rehash immediately before attaching; inspect preselected portal attachments.
If bytes change, release the new version and update its manifest. A filename or
hash alone proves neither truth nor approval. Never rewrite, reformat, convert or
manufacture a transcript; use the owner's unchanged, explicitly authorized file.

## Receipt and provenance

Record what actually went to the employer, with exact hashes and the operator's
observations. The `receipt` command requires nonempty evidence and the submitted
resume, a matching-confirmation count of one and an identity-verification flag.
Those inputs are operator attestations: software does not establish inbox identity
or employer provenance. Preserve genuine evidence before updating the ledger.

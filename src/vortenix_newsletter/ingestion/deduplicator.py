from vortenix_newsletter.domain.models import SourceDocument
def deduplicate(documents: list[SourceDocument])->list[SourceDocument]:
    seen=set(); result=[]
    for item in documents:
        key=(str(item.url),item.content_hash)
        if key not in seen: seen.add(key); result.append(item)
    return result

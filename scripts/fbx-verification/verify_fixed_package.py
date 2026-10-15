"""Verify an already locally reviewed package by exact hashes, not raw QA replay.

The raw local report stays private. Its separately reviewed package metadata is
frozen in F; fresh CI QA is checked separately by verify_fbx_report.
"""
import io,json,stat,zipfile
from verify_fbx_report import need,digest,relative
NAMES={'README.md','asset.json','CONVERSION.json','CONVERSION_NOTES.md','LICENSE.txt','ATTRIBUTION.txt','FILES.sha256'}
def verify_fixed_package(blob,identity,fbx,expected,inputs,source,license_bytes,notes_bytes):
 need(len(blob)==expected['archiveBytes'] and digest(blob)==expected['archiveSha256'],'Reviewed archive hash mismatch')
 need(len(fbx)==expected['fbxBytes'] and digest(fbx)==expected['fbxSha256'],'Reviewed FBX hash mismatch')
 need(set(inputs)==NAMES,'Frozen metadata names mismatch')
 for name,b in inputs.items():need(digest(b)==expected['packageInputs'][name],'Frozen metadata hash mismatch')
 allbytes={**inputs,identity+'.fbx':fbx}
 with zipfile.ZipFile(io.BytesIO(blob)) as z:
  infos=z.infolist();need(len(infos)==8 and {i.filename for i in infos}=={identity+'/'+n for n in allbytes},'Exact eight-entry package required')
  need(sum(i.file_size for i in infos)==sum(len(b) for b in allbytes.values()),'ZIP uncompressed size mismatch')
  for i in infos:
   name=i.filename.split('/',1)[1];need(relative(i.filename) and i.flag_bits&1==0 and stat.S_IFMT(i.external_attr>>16) in (0,stat.S_IFREG) and not (i.external_attr>>16)&0o111,'Unsafe archive entry')
   need(i.date_time==(2026,10,15,0,0,0) and i.compress_type==zipfile.ZIP_DEFLATED and i.create_system==3 and i.external_attr==0o644<<16,'Archive profile mismatch')
   need(i.file_size==len(allbytes[name]) and z.read(i)==allbytes[name],'ZIP entry differs from frozen bytes')
 lines=inputs['FILES.sha256'].decode().splitlines();listed={}
 for line in lines:
  need(len(line)>66 and line[64:66]=='  ','Malformed FILES.sha256');h,name=line[:64],line[66:];need(name in allbytes and name!='FILES.sha256' and name not in listed,'Invalid FILES entry');need(digest(allbytes[name])==h,'FILES hash mismatch');listed[name]=h
 need(set(listed)==set(allbytes)-{'FILES.sha256'},'FILES must cover all seven non-self entries')
 need(inputs['LICENSE.txt']==license_bytes and inputs['CONVERSION_NOTES.md']==notes_bytes,'License or notes changed')
 attrs=json.loads(inputs['asset.json']);conv=json.loads(inputs['CONVERSION.json'])
 for k in ('id','title','titleEn','description','descriptionEn','author','license','version','unit','upAxis','dimensions','triangles'):
  if k in source:need(attrs.get(k)==source[k],'Source metadata mismatch '+k)
 need(source['id']==identity and source['status']=='public' and source['license']=='CC-BY-4.0','Source cohort mismatch')
 need(attrs['originalModelStatus']=='public' and attrs['sourceGlbSha256']==conv['sourceGlbSha256']==expected['sourceGlbSha256'],'Source GLB provenance mismatch')
 need(conv['id']==identity and conv['fbxSha256']==attrs['fbxSha256']==expected['fbxSha256'] and conv['fbxBytes']==len(fbx),'Package derivative provenance mismatch')
 need(conv['pipelineSha256']=='89cdfcdcb1d84495c2fcecf34d944143a38137488dd62ef7b510a6b8576249ac' and conv['unityTested'] is False and attrs['unityTested'] is False,'Package limits/provenance mismatch')
 for name in NAMES:
  text=inputs[name].decode();need(not any(x in text for x in ('/workspace/','/tmp/','/home/','/Users/','file://')),'Private path in fixed metadata')
 return {'packageEvidence':'hash-identical reviewed-local package','reviewedLocalReportSha256':expected['reviewedQaSha256'],'archiveSha256':digest(blob),'entryCount':8}

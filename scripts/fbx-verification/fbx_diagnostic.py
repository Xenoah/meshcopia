"""Read-only FBX7400 structure hashes; never prints string/property contents."""
import hashlib,json,struct,zlib

def sha(b):return hashlib.sha256(b).hexdigest()
def signatures(data):
 if data[:23]!=b'Kaydara FBX Binary  \x00\x1a\x00' or struct.unpack_from('<I',data,23)[0]!=7400:raise ValueError('Expected FBX7400')
 out={};limits={'Y':2,'C':1,'I':4,'F':4,'D':8,'L':8};arrays={'f':4,'d':8,'l':8,'i':4,'b':1,'c':1}
 def node(start,parent,ordinal):
  end,count,plen=struct.unpack_from('<III',data,start);size=data[start+12]
  if end==0:return start+13
  if not(start<end<=len(data)) or count>100000:raise ValueError('Invalid bounds')
  tag=data[start+13:start+13+size].decode('ascii');path=parent+'/'+tag+'['+str(ordinal)+']';pos=start+13+size
  props=[]
  for _ in range(count):
   begin=pos;t=chr(data[pos]);pos+=1
   if t in limits:raw=data[pos:pos+limits[t]];pos+=limits[t];semantic=raw
   elif t in ('S','R'):
    n=struct.unpack_from('<I',data,pos)[0];pos+=4;raw=data[pos:pos+n];pos+=n;semantic=raw
   elif t in arrays:
    n,enc,sz=struct.unpack_from('<III',data,pos);pos+=12;raw=data[pos:pos+sz];pos+=sz;semantic=zlib.decompress(raw) if enc==1 else raw
    if len(semantic)!=n*arrays[t]:raise ValueError('Array size mismatch')
   else:raise ValueError('Unsupported property type')
   if pos>end:raise ValueError('Property exceeds bounds')
   props.append({'type':t,'bytes':len(semantic),'semanticSha256':sha(semantic),'encodedSha256':sha(data[begin:pos])})
  out[path]=props;i=0
  while pos<end-13:pos=node(pos,path,i);i+=1
  return end
 pos=27;i=0
 while any(data[pos:pos+13]):pos=node(pos,'',i);i+=1
 out['footer']=[{'bytes':len(data[pos:]),'sha256':sha(data[pos:])}]
 return {'bytes':len(data),'sha256':sha(data),'nodes':out}
def compare(data,baseline):
 actual=signatures(data);different=[]
 for p in sorted(set(actual['nodes'])|set(baseline['nodes'])):
  if actual['nodes'].get(p)!=baseline['nodes'].get(p):different.append({'node':p,'expected':baseline['nodes'].get(p),'actual':actual['nodes'].get(p)})
 return {'expectedSha256':baseline['sha256'],'actualSha256':actual['sha256'],'expectedBytes':baseline['bytes'],'actualBytes':actual['bytes'],'differentNodes':len(different),'details':different[:40]}

"""Four original public-office document-service props. Xenoah, CC BY 4.0.
Static external appearance, with real feed openings and no functioning mechanisms.
Authoring Z-up metres; immutable common.py exports self-contained Y-up GLB + STL.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import *


def palette():
    return dict(ivory=mat('Warm ivory molded housing',(.68,.70,.67),.08,.38),
        grey=mat('Cool grey equipment shell',(.26,.31,.33),.18,.43),
        dark=mat('Graphite internal fittings',(.045,.061,.070),.15,.48),
        black=mat('Matte rubber contact surfaces',(.014,.020,.024),0,.78),
        metal=mat('Satin machined metal',(.49,.56,.59),.78,.32),
        blue=mat('Muted teal enamel',(.055,.22,.25),.20,.40),
        screen=mat('Opaque inactive display glass',(.014,.060,.076),.18,.24),
        red=mat('Muted red control',(.55,.055,.035),0,.42),
        green=mat('Unlit green indicator',(.035,.30,.13),0,.34),
        paper=mat('Unmarked paper appearance',(.82,.83,.77),0,.72))


def cyl(name, pos, radius, depth, material, axis='Z', n=24, bevel=.001):
    o=cylinder(name,pos,radius,depth,material,vertices=n,bevel=bevel)
    if axis=='X':o.rotation_euler[1]=math.pi/2
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    for face in o.data.polygons:face.use_smooth=len(face.vertices)==4
    for mod in o.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return o


def rod(name,a,b,radius,material,n=20):
    a,b=Vector(a),Vector(b)
    o=cyl(name,(a+b)/2,radius,(b-a).length,material,n=n,bevel=min(.0007,radius*.1))
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def bar(name,a,b,width,depth,material,bevel=.003):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)/2,(width,depth,(b-a).length),material,bevel)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o


def prism_x(name,profile,x,width,material,bevel=.003):
    vs=[(xx,y,z) for xx in [x-width/2,x+width/2] for y,z in profile];n=len(profile)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bevel)


def screw(name,pos,material,axis='Z',r=.004):
    return cyl(name,pos,r,.003,material,axis,n=8,bevel=.0003)


def pull(name,x,y,z,width,p,depth=.025):
    for xx in [x-width/2+.012,x+width/2-.012]:box(name+' stand-off',(xx,y+.009,z),( .018,depth,.018),p['grey'],.003)
    box(name+' grip',(x,y-depth/2,z),(width,.019,.023),p['grey'],.006)


def socket(name,x,y,z,width,height,p):
    # Four closed perimeter solids define a real recessed connector mouth.
    for xx in [x-width/2,x+width/2]:box(name+' side',(xx,y,z),(.004,.017,height+.004),p['metal'],.0007)
    for zz in [z-height/2,z+height/2]:box(name+' lip',(x,y,zz),(width-.002,.017,.004),p['metal'],.0007)
    box(name+' interior rear',(x,y-.009,z),(width-.005,.002,height-.004),p['dark'],.0005)


def caster(name,x,y,z,p,r=.029):
    # Contact point is z-r; swivel fork sits above the wheel.
    cyl(name+' wheel',(x,y,z),r,.026,p['black'],'X',28,.002)
    for xx in [x-.019,x+.019]:
        box(name+' fork cheek',(xx,y,z+.012),(.009,.033,.050),p['metal'],.003)
        cyl(name+' axle cap',(xx+(.006 if xx>x else -.006),y,z),.008,.004,p['grey'],'X',16,.0005)
    cyl(name+' swivel stem',(x,y,z+.047),.012,.027,p['metal'],n=20)
    cyl(name+' mounting swivel',(x,y,z+.055),.021,.012,p['dark'],n=24)


def copier():
    p=palette()
    for x in [-.238,.238]:
        for y in [-.238,.238]:caster('Copier caster',x,y,.035,p,r=.035)
    box('Copier lower chassis',(0,0,.116),(.58,.59,.050),p['dark'],.009)
    # Shell walls leave the output bay genuinely open at the front.
    for x in [-.281,.281]:box('Copier full-height side shell',(x,.005,.469),(.042,.60,.66),p['ivory'],.012)
    box('Copier rear spine',(0,.278,.486),(.53,.055,.70),p['grey'],.008)
    box('Copier cassette rear body',(0,.015,.405),(.53,.515,.52),p['ivory'],.009)
    for z,height in [(.253,.205),(.463,.205),(.633,.120)]:
        box('Individual paper cassette front',(0,-.271,z),(.528,.046,height),p['ivory'],.006)
        # The pull is an open arch, separated from the cassette face.
        pull('Cassette pull',0,-.310,z+height*.18,.20,p)
        box('Blank cassette index recess',(-.198,-.296,z-.030),(.055,.004,.022),p['grey'],.001)
        box('Blank cassette index insert',(-.198,-.299,z-.030),(.042,.002,.012),p['paper'],.0005)
    # Exit bay floor, rear stop and ceiling surround a visible, unsealed cavity.
    prism_x('Paper output receiving floor',[(-.310,.713),(-.310,.727),(.155,.752),(.185,.752),(.185,.714)],0,.520,p['grey'],.004)
    box('Output bay rear wall',(0,.192,.795),(.52,.030,.155),p['dark'],.004)
    box('Output overhead bridge',(0,-.012,.890),(.61,.62,.066),p['ivory'],.012)
    for x in [-.205,-.10,0,.10,.205]:box('Output tray raised guide rib',(x,-.050,.746),(.006,.32,.007),p['ivory'],.002,rot=(math.radians(3),0,0))
    cyl('Visible exit roller',(0,.165,.822),.018,.415,p['black'],'X',32,.001)
    for x in [-.218,.218]:box('Exit roller support',(x,.17,.818),(.020,.035,.055),p['grey'],.003)
    # Scanner slab, hinge barrels and a raised automatic document feeder.
    box('Scanner platen lower housing',(0,-.004,.947),(.635,.637,.053),p['grey'],.012)
    box('Scanner lid perimeter',(0,-.004,.979),(.628,.630,.025),p['ivory'],.009)
    for x in [-.22,.22]:
        box('Scanner hinge mounting',(x,.306,.955),(.073,.040,.045),p['dark'],.005)
        cyl('Scanner hinge barrel',(x,.321,.978),.018,.072,p['metal'],'X',24,.001)
    # Feeder side cheeks are a low tunnel, not a solid decorative box.
    for x in [-.255,.255]:prism_x('Feeder tunnel cheek',[(-.22,.998),(-.22,1.070),(-.15,1.105),(.24,1.105),(.27,1.035),(.27,.998)],x,.045,p['ivory'],.007)
    box('Feeder overhead cover',(0,.092,1.089),(.49,.337,.040),p['ivory'],.010)
    prism_x('Feeder lower paper deck',[(-.265,1.009),(-.265,1.021),(.18,1.027),(.22,1.006)],0,.485,p['grey'],.003)
    cyl('Feeder pickup roller',(0,.008,1.052),.015,.37,p['black'],'X',28,.001)
    for x in [-.159,.159]:box('Feeder sliding paper side guide',(x,-.129,1.045),(.014,.200,.048),p['blue'],.004)
    # Right-front tilted interface, with all face details transformed together.
    rod('Copier console support',(.247,-.245,.925),(.322,-.333,1.040),.020,p['dark'],24)
    loc=Vector((.323,-.365,1.065));rot=math.radians(32)
    def panel(name,offset,size,material,bev):
        v=Vector(offset);q=Vector((v.x,math.cos(rot)*v.y-math.sin(rot)*v.z,math.sin(rot)*v.y+math.cos(rot)*v.z));return box(name,loc+q,size,material,bev,rot=(rot,0,0))
    panel('Raised operator interface',(0,0,0),(.247,.155,.026),p['dark'],.010)
    panel('Blank inactive copier display',(-.035,0,.016),(.135,.109,.006),p['screen'],.003)
    for x in [.064,.090]:
        for y in [-.030,0,.030]:panel('Copier control key',(x,y,.017),(.016,.018,.007),p['ivory'],.002)
    panel('Copier start button',(.077,-.056,.018),(.041,.018,.008),p['blue'],.003)
    # Right service panel and rear connectors, vents, fasteners and cable restraint.
    box('Right service door',(.305,.039,.469),(.012,.43,.50),p['ivory'],.005)
    box('Right service latch',(.316,-.126,.604),(.012,.063,.023),p['grey'],.002)
    box('Rear lower electrical panel',(0,.311,.310),(.45,.017,.250),p['dark'],.006)
    socket('Recessed power inlet',-.125,.327,.250,.047,.031,p)
    for x in [-.135,-.119,-.103]:box('Power inlet pin',(x,.323,.250),(.003,.010,.007),p['metal'],.0005)
    socket('Data connector',.095,.327,.327,.035,.025,p)
    socket('Service connector',.150,.327,.327,.025,.015,p)
    for x in [-.195,.195]:
        for z in [.225,.400]:screw('Rear cover fastener',(x,.323,z),p['metal'],'Y')
    for z in [.515,.540,.565,.590,.615]:box('Rear raised ventilation louvre',(0,.317,z),(.37,.025,.011),p['grey'],.002)
    box('Rear ventilation shadow recess',(0,.307,.565),(.385,.008,.135),p['dark'],.001)
    for x in [-.245,.245]:box('Underside reinforcement',(x,0,.087),(.025,.43,.018),p['metal'],.003)
    box('Copier underside access cover',(0,0,.091),(.405,.405,.014),p['grey'],.004)
    for x in [-.174,.174]:
        for y in [-.174,.174]:screw('Copier underside cover screw',(x,y,.083),p['metal'],r=.004)
    return ('city-office-multifunction-copier','オフィス用複合コピー機','Office multifunction copier',
        '公共施設の事務室・コピー室向けの複合機外観。三段の用紙カセットと開いた取っ手、実形状の排紙空間・ローラー・受け皿、スキャナー蓋とヒンジ、開口した原稿送り部、支持腕付き無表示操作盤、側面扉、背面接続口とキャスターを造形。原稿・印刷物や内部印刷機構は付属せず、読取り・印刷・給排紙・電気機能はありません。安全性・機器性能や認証は示しません。',
        'A multifunction-copier exterior for civic office and copy-room interiors. Features three paper cassettes with open pulls, a genuinely open output bay with roller and receiving tray, scanner lid/hinges, open document-feeder throat, supported inactive control panel, side service door, rear connectors and casters. No loose documents or internal print mechanism are included; scanning, printing, paper transport and electrical functions are absent. No safety, performance or certification claims.',
        ['office','copier','document','public-facility','複合機'])


def paper_cutter():
    p=palette()
    for x in [-.195,.195]:
        for y in [-.245,.245]:cyl('Paper cutter rubber foot',(x,y,.014),.026,.028,p['black'],n=24,bevel=.003)
    box('Cutter table folded base',(0,0,.048),(.48,.66,.062),p['blue'],.014)
    box('Paper alignment work surface',(-.014,0,.084),(.432,.625,.012),p['ivory'],.005)
    # Unnumbered alignment lines are visual references, not calibrated measurements.
    for x in [-.17,-.105,-.040,.025,.090]:box('Unnumbered longitudinal alignment line',(x,0,.091),(.0015,.595,.0010),p['grey'],.0002)
    for y in [-.25,-.17,-.09,-.01,.07,.15,.23]:box('Unnumbered transverse alignment line',(-.035,y,.091),(.389,.0015,.0010),p['grey'],.0002)
    box('Rear paper squaring fence',(-.020,.269,.111),(.428,.021,.046),p['metal'],.003)
    box('Left measuring stop track',(-.227,-.005,.099),(.017,.56,.021),p['metal'],.002)
    box('Adjustable paper stop carriage',(-.218,-.112,.117),(.044,.070,.026),p['dark'],.003)
    box('Fixed-position movable paper stop',(-.025,-.112,.119),(.390,.019,.055),p['blue'],.004)
    cyl('Stop lock knob',(-.221,-.112,.145),.019,.025,p['dark'],n=24,bevel=.003)
    # Right-side fixed cutting bed and pivot assembly.
    box('Stationary cutting bed',(.230,0,.095),(.028,.650,.018),p['metal'],.002)
    for y in [-.285,.285]:screw('Cutting bed fastener',(.230,y,.106),p['dark'],r=.004)
    box('Rear guillotine hinge pedestal',(.253,.300,.126),(.060,.065,.095),p['blue'],.007)
    pivot=Vector((.260,.292,.164));angle=math.radians(26);length=.70
    end=pivot+Vector((0,-length*math.cos(angle),length*math.sin(angle)))
    # Raised blade spine and separate blunt bevel strip share the same fixed pose.
    profile=[(.292,.154),(.292,.183),(end.y,end.z+.019),(end.y,end.z-.021)]
    prism_x('Raised guillotine blade spine',profile,.257,.018,p['grey'],.003)
    prism_x('Visible blunt blade bevel',[(.289,.153),(.289,.158),(end.y+.035,end.z-.012),(end.y+.035,end.z-.021)],.245,.006,p['metal'],.0008)
    cyl('Blade hinge pivot',pivot,.028,.086,p['metal'],'X',32,.0015)
    cyl('Outer pivot washer',(.310,.292,.164),.031,.009,p['dark'],'X',28,.001)
    screw('Pivot axle fastener',(.318,.292,.164),p['metal'],'X',r=.011)
    grip_start=pivot+Vector((0,-.56*math.cos(angle),.56*math.sin(angle)))
    grip_end=pivot+Vector((0,-.765*math.cos(angle),.765*math.sin(angle)))
    rod('Raised guillotine handle core',grip_start,grip_end,.014,p['metal'],24)
    rod('Molded guillotine hand grip',grip_start+Vector((0,-.035,.017)),grip_end,.026,p['dark'],32)
    cyl('Lever rest bumper',(.258,-.306,.102),.017,.022,p['black'],n=20)
    # Fixed slotted finger-guard fence: genuine open spaces, not a painted panel.
    box('Finger guard lower rail',(.189,-.005,.122),(.013,.578,.014),p['grey'],.003)
    box('Finger guard upper rail',(.189,-.005,.202),(.014,.578,.018),p['grey'],.004)
    for y in [-.277,-.165,-.053,.059,.171,.277]:box('Finger guard upright',(.189,y,.162),(.013,.011,.076),p['grey'],.002)
    for y in [-.276,.276]:
        box('Finger guard mounting shoe',(.179,y,.104),(.043,.034,.019),p['metal'],.002)
        screw('Finger guard mount screw',(.165,y,.117),p['dark'],r=.004)
    # Underside fold flanges and a transverse stiffener remain visible below.
    for x in [-.194,.194]:box('Cutter underside folded rail',(x,0,.022),(.018,.49,.023),p['grey'],.003)
    box('Cutter underside cross brace',(0,0,.022),(.35,.029,.022),p['grey'],.003)
    for x in [-.145,.145]:
        for y in [-.205,.205]:screw('Cutter underside screw',(x,y,.0165),p['metal'],r=.004)
    return ('city-guillotine-paper-cutter','レバー式ペーパーカッター','Guillotine paper cutter',
        '役所・図書館の作業台やコピー室に置くレバー式裁断器の静的外観。脚付きテーブル、数字のない位置合わせ線、後端フェンス、固定位置の可動ストッパーとロックつまみ、上げた刃・握り・軸、隙間を持つ固定ガードと下面補強を造形。目盛りの精度や実際の裁断・ガード動作はなく、刃は表示用の厚みを持つ形状です。安全性・切断性能や認証は示しません。',
        'A static lever paper-cutter prop for public-office, library and copy-room worktops. Includes a footed table, unnumbered alignment lines, rear fence, fixed-position adjustable stop/lock knob, raised blade/handle/pivot, open fixed guard and underside stiffeners. Alignment marks are not calibrated; cutting and guard operation are absent, and the blade has deliberately finite visual thickness. No safety, cutting-performance or certification claims.',
        ['office','paper-cutter','guillotine','document','ペーパーカッター'])


def shredder():
    p=palette()
    for x in [-.135,.135]:
        for y in [-.099,.099]:caster('Shredder caster',x,y,.022,p,r=.022)
    box('Shredder base cradle',(0,0,.086),(.355,.278,.045),p['dark'],.009)
    # Open-topped removable collection bin, with a real narrow sight opening.
    box('Bin floor',(0,-.003,.124),(.309,.243,.028),p['blue'],.006)
    for x in [-.146,.146]:box('Bin side wall',(x,-.004,.285),(.024,.238,.312),p['blue'],.006)
    box('Bin rear wall',(0,.107,.285),(.29,.023,.312),p['blue'],.005)
    # Four front pieces surround the vertical window, leaving the inner bin visible.
    for x,w in [(-.100,.106),(.100,.106)]:box('Bin front side around sight window',(x,-.119,.283),(w,.025,.312),p['blue'],.005)
    box('Bin window lower surround',(0,-.119,.166),(.095,.025,.079),p['blue'],.004)
    box('Bin window upper surround',(0,-.119,.394),(.095,.025,.090),p['blue'],.004)
    # Metal frame around the opening is inset, with no opaque panel blocking the hole.
    for x in [-.046,.046]:box('Sight opening vertical trim',(x,-.136,.277),(.007,.009,.152),p['grey'],.0015)
    for z in [.202,.352]:box('Sight opening horizontal trim',(0,-.136,z),(.096,.009,.007),p['grey'],.0015)
    pull('Removable bin pull',0,-.155,.405,.135,p,.028)
    box('Bin lower toe recess',(0,-.139,.141),(.165,.010,.016),p['dark'],.002)
    # Chassis sides support a clearly separate cutter head above the removable bin.
    for x in [-.165,.165]:box('Cutter head support column',(x,.052,.308),(.026,.155,.410),p['grey'],.007)
    box('Cutter rear support web',(0,.127,.312),(.305,.022,.410),p['grey'],.006)
    box('Cutter lower front lip',(0,-.112,.471),(.339,.060,.026),p['dark'],.005)
    box('Cutter lower rear lip',(0,.095,.471),(.339,.085,.026),p['dark'],.005)
    # A real separated feed slot runs between front and rear upper covers.
    prism_x('Shredder front sloped feed surface',[(-.151,.477),(-.151,.519),(-.125,.550),(-.012,.550),(-.012,.532),(-.085,.513),(-.085,.477)],0,.370,p['ivory'],.007)
    prism_x('Shredder rear sloped feed surface',[(.012,.532),(.012,.550),(.123,.550),(.151,.521),(.151,.477),(.080,.477),(.080,.513)],0,.370,p['ivory'],.007)
    for x in [-.172,.172]:box('Shredder feed slot end cheek',(x,0,.526),(.026,.045,.055),p['ivory'],.005)
    # Paired fixed feed rollers leave an actual narrow paper path between them.
    for y in [-.018,.018]:cyl('Fixed shredder feed roller',(0,y,.514),.012,.303,p['black'],'X',28,.0007)
    box('Shredder selector base',(.105,-.094,.551),(.068,.025,.007),p['grey'],.002)
    box('Shredder fixed selector tab',(.098,-.094,.559),(.023,.023,.011),p['dark'],.002)
    for x in [-.096,-.073]:cyl('Unlit shredder indicator',(x,-.094,.553),.005,.004,p['green'] if x<-.08 else p['red'],n=16,bevel=.0005)
    # Rear service detail and underside plate are secondary but actual geometry.
    box('Shredder rear motor panel',(0,.148,.484),(.265,.012,.045),p['dark'],.004)
    socket('Shredder power connection',-.086,.158,.487,.031,.020,p)
    for x in [-.131,.131]:screw('Shredder motor cover screw',(x,.157,.486),p['metal'],'Y',r=.003)
    for x in [-.080,0,.080]:box('Shredder underside reinforcing rib',(x,0,.060),(.014,.172,.012),p['grey'],.002)
    for x in [-.134,.134]:
        for y in [-.084,.084]:screw('Shredder base screw',(x,y,.062),p['metal'],r=.003)
    return ('city-document-shredder','事務用シュレッダー','Office document shredder',
        '事務室・公共窓口のバックヤード向けのシュレッダー外観。分かれた傾斜給紙面と実開口の投入口、固定給紙ローラー、独立した裁断ヘッド外装、取っ手付きの開放上面回収箱と実開口の確認窓、支持枠・キャスター・背面接続口を造形。窓ガラス、裁断歯、紙片は付属せず、箱・ローラーは固定されています。給紙・裁断・電気動作や安全・情報破棄性能の検証、認証はありません。',
        'A document-shredder exterior for office and civic-service back rooms. Features split sloping feed surfaces around a genuine inlet, fixed feed rollers, a separate cutter-head exterior, open-topped removable-bin form with pull and real sight opening, support frame, casters and rear connection. Window glazing, cutting teeth and paper scraps are not included; bin and rollers remain fixed. No feeding, shredding or electrical behavior, safety/data-destruction validation or certification.',
        ['office','shredder','document','public-facility','シュレッダー'])


def laminator():
    p=palette()
    for x in [-.171,.171]:
        for y in [-.071,.071]:cyl('Laminator rubber foot',(x,y,.0095),.016,.019,p['black'],n=24,bevel=.0018)
    # Lower body and upper arched hood are separated at both inlet and outlet.
    prism_x('Laminator lower tray chassis',[(-.118,.018),(-.118,.039),(-.089,.048),(.089,.048),(.118,.038),(.118,.018)],0,.410,p['grey'],.006)
    prism_x('Laminator arched upper hood',[(-.104,.075),(-.098,.098),(-.072,.115),(.069,.115),(.098,.098),(.104,.075),(.076,.075),(.061,.088),(-.061,.088),(-.076,.075)],0,.352,p['ivory'],.007)
    for x in [-.192,.192]:prism_x('Laminator full side cap',[(-.112,.033),(-.108,.083),(-.082,.113),(.082,.113),(.110,.082),(.112,.033)],x,.039,p['blue'],.008)
    # Inlet and outlet lips with real gap into a paired static roller path.
    for y in [-.106,.106]:
        box('Laminator lower paper entry lip',(0,y,.049),(.349,.024,.008),p['dark'],.002)
        box('Laminator upper throat lip',(0,y,.076),(.349,.014,.008),p['grey'],.002)
    for y in [-.047,.047]:
        cyl('Laminator lower roller',(0,y,.054),.014,.345,p['black'],'X',32,.001)
        cyl('Laminator upper roller',(0,y,.087),.014,.345,p['black'],'X',32,.001)
        for x in [-.177,.177]:cyl('Laminator roller bearing end',(x,y,.0705),.028,.012,p['metal'],'X',24,.001)
    # Very thin internal guide strips sit below the paper path, not across it.
    for x in [-.125,0,.125]:box('Laminator lower path guide',(x,0,.059),(.007,.056,.004),p['metal'],.0008)
    for x in [-.145,.145]:box('Unnumbered inlet guide stripe',(x,-.100,.054),(.003,.019,.0015),p['ivory'],.0002)
    # Controls on right endcap, away from the feed span; no fabricated temperature scale.
    box('Laminator rocker bezel',(.194,-.045,.117),(.023,.040,.007),p['dark'],.002)
    box('Laminator fixed rocker',(.194,-.045,.122),(.016,.028,.007),p['grey'],.002,rot=(math.radians(7),0,0))
    for y in [.014,.043]:cyl('Unlit laminator indicator',(.192,y,.117),.005,.004,p['green'] if y>0.03 else p['red'],n=16,bevel=.0004)
    box('Laminator release lever exterior',(-.192,.094,.076),(.023,.035,.016),p['dark'],.003)
    # Rear power socket is positioned in an endcap, not across the sheet outlet.
    socket('Laminator recessed power inlet',.193,.115,.054,.022,.017,p)
    for x in [-.147,.147]:
        for y in [-.060,.060]:screw('Laminator underside assembly screw',(x,y,.017),p['metal'],r=.003)
    for y in [-.043,0,.043]:box('Laminator underside stiffening rib',(0,y,.014),(.270,.007,.009),p['dark'],.0015)
    return ('city-desktop-document-laminator','卓上書類ラミネーター','Desktop document laminator',
        '図書館・学校事務室・公共施設の作業台向けの卓上ラミネーター外観。アーチ状上カバーと下トレー、左右端部、別々に開いた前方投入・後方排出の喉部、間隔のある上下固定ローラーと案内条、無表示操作部、解除レバー外装、後部接続口・下面ねじ・ゴム脚を造形。フィルムや書類は付属せず、搬送・加熱・温度制御・解除機能はありません。安全性・ラミネート性能や認証は示しません。',
        'A desktop laminator exterior for library, school-office and civic-facility worktops. Includes an arched upper hood/lower tray, side caps, separately open front inlet and rear outlet throats, spaced fixed upper/lower rollers and guide strips, unmarked controls, release-lever exterior, rear connection, underside screws and rubber feet. No film or documents are included; transport, heating, temperature control and release functions are absent. No safety, lamination-performance or certification claims.',
        ['office','laminator','document','desktop','ラミネーター'])


BUILDERS=[copier,paper_cutter,shredder,laminator]
if __name__=='__main__':
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--out',default='batches/batch-030/assets');p.add_argument('--only',default='');p.add_argument('--geometry-only',action='store_true');a=p.parse_args(argv)
    out=Path(a.out);out=out if out.is_absolute() else ROOT/out
    if a.geometry_only:common.render=lambda *args,**kwargs:None
    for fn in BUILDERS:
        reset();spec=fn()
        if a.only and spec[0]!=a.only:continue
        publish_asset(*spec,out,'scripts/city_expansion/document_service_equipment.py',azimuth=(125 if spec[0]=='city-guillotine-paper-cutter' else -55),elevation=(28 if spec[0]=='city-office-multifunction-copier' else 25))

import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const requireFromRuntime=createRequire(path.join(process.env.RUNTIME_NODE_MODULES,'__runtime__.cjs'));
const {Presentation,PresentationFile}=await import(pathToFileURL(requireFromRuntime.resolve('@oai/artifact-tool')).href);
const root=process.cwd();
const content=JSON.parse(await fs.readFile(path.join(root,process.argv[3] || 'scripts/midpoint_content.json'),'utf8'));
const tableOwners=content.flatMap((item,i)=>item.table ? [i+1] : []);
const p=Presentation.create({slideSize:{width:1280,height:720}});
for (const item of content){
 const s=p.slides.add(); s.background.fill='#F7F5F0'; s.speakerNotes.text=item.notes;
 for(const box of item.boxes){
  let y=box.y;
  for(const value of box.paragraphs){
   if(!value) continue;
   const lines=Math.ceil(value.length/(box.w/(box.size*.48)));
   const h=Math.max(box.size*1.3,lines*box.size*1.25);
   const shape=s.shapes.add({geometry:'textbox',position:{left:box.x,top:y,width:box.w,height:Math.min(h,box.h)},fill:'none',line:{fill:'none',width:0}});
   shape.text=value;shape.text.style={fontFamily:'Aptos',fontSize:box.size,bold:box.bold,color:box.color};
   y+=h+18;
  }
 }
 if(item.table){
  const table=s.tables.add({rows:item.table.length,columns:item.table[0].length,...(item.table_position || {left:76.8,top:163.2,width:1123.2,height:451.2}),columnWidths:item.table_widths || [158.4,633.6,331.2],values:item.table});
  table.cells.block({row:0,column:0,rowCount:item.table.length,columnCount:item.table[0].length}).assign({fill:'#F7F5F0',textStyle:{fontFamily:'Aptos',fontSize:item.table_font_size || 25.33,color:'#24342E'}});
  table.cells.block({row:0,column:0,rowCount:1,columnCount:item.table[0].length}).assign({fill:'#29695B',textStyle:{fontFamily:'Aptos',fontSize:item.table_font_size || 25.33,bold:true,color:'#FFFFFF'}});
 }
}
await (await PresentationFile.exportPptx(p)).save(path.join(root,'.build/midpoint_real_candidate.pptx'));
const {finalizePresentation}=await import('file:///Users/alina/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations/container_tools/artifact_tool_utils.mjs');
const skill='/Users/alina/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
await finalizePresentation({workspaceDir:root,candidatePath:path.join(root,'.build/midpoint_real_candidate.pptx'),finalPath:path.join(root,'output/presentation/'+(process.argv[2] || 'midpoint_real_data.pptx')),pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:content.length,requiredNativeTableOwnerSlides:tableOwners,fontPolicy:{basis:'design',families:['Aptos']},verifyArtifactToolImport:true,receiptPath:path.join(root,'.build/'+(process.argv[2] || 'midpoint_real_data.pptx')+'.validation.json')});

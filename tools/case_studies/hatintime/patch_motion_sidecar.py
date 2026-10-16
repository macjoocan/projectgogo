from pathlib import Path
p=Path(__file__).resolve().parent/'tools/source/UEViewer-master';f=p/'Exporters/ExportMd5.cpp';s=f.read_text()
s=s.replace('#include "UnMaterial.h"','#include "UnMaterial.h"\n#if UNREAL3\n#include "UnMesh3.h"\n#endif',1)
marker='void ExportMd5Anim(const CAnimSet *Anim)'
fn=r'''
// Local research extension: preserve source UE3 scale tracks and compression metadata.
// This is not a claim that legacy MD5 has native scale-animation support.
static void ExportHatSourceMotion(const CAnimSet *Anim)
{
#if UNREAL3 && HAT
 UObject *Obj = Anim->OriginalAnim;
 if (!Obj || !Obj->IsA("AnimSet")) return;
 UAnimSet *Set = (UAnimSet*)Obj;
 if (Set->Package->Game != GAME_HAT) return;
 for (int n=0; n<Set->Sequences.Num(); n++)
 {
  UAnimSequence *Seq=Set->Sequences[n]; if (!Seq) continue;
  FArchive *Out=CreateExportArchive(Obj,FAO_TextFile,"%s/%s.source.json",Obj->Name,*Seq->SequenceName);
  if (!Out) continue;
  Out->Printf("{\"sequence\":\"%s\",\"object\":\"%s\",\"export_index\":%d,\"frames\":%d,\"sequence_length\":%.9g,\"rate_scale\":%.9g,\"scale_compression\":%d,\"key_encoding\":%d,\"without_translations\":%s,\"rotation_only\":%s,\"additive\":%s,\"scale_offsets\":[",*Seq->SequenceName,Seq->Name,Seq->PackageIndex,Seq->NumFrames,Seq->SequenceLength,Seq->RateScale,(int)Seq->ScaleCompressionFormat,(int)Seq->KeyEncodingFormat,Seq->bWasCompressedWithoutTranslations?"true":"false",Set->bAnimRotationOnly?"true":"false",Seq->bIsAdditive?"true":"false");
  int active=0;
  for (int k=0;k<Seq->CompressedScaleOffsets.Num();k++){if(k)Out->Printf(",");Out->Printf("%d",Seq->CompressedScaleOffsets[k]);if(Seq->CompressedScaleOffsets[k]>=0)active++;}
  Out->Printf("],\"compressed_track_offsets\":[");
  for(int k=0;k<Seq->CompressedTrackOffsets.Num();k++){if(k)Out->Printf(",");Out->Printf("%d",Seq->CompressedTrackOffsets[k]);}
  Out->Printf("],\"tracks\":[");
  int nonunit=0;
  for(int k=0;k<Seq->RawAnimData.Num();k++)
  {
   if(k)Out->Printf(",");const FRawAnimSequenceTrack &T=Seq->RawAnimData[k];
   Out->Printf("{\"bone\":\"%s\",\"raw_position_count\":%d,\"raw_rotation_count\":%d,\"scale\":[",k<Set->TrackBoneNames.Num()?*Set->TrackBoneNames[k]:"UNMAPPED",T.PosKeys.Num(),T.RotKeys.Num());
   for(int j=0;j<T.ScaleKeys.Num();j++){if(j)Out->Printf(",");const FVector &V=T.ScaleKeys[j];Out->Printf("[%.9g,%.9g,%.9g]",V.X,V.Y,V.Z);if(V.X!=1||V.Y!=1||V.Z!=1)nonunit++;}
   Out->Printf("]}");
  }
  Out->Printf("],\"use_translation_bones\":[");for(int k=0;k<Set->UseTranslationBoneNames.Num();k++){if(k)Out->Printf(",");Out->Printf("\"%s\"",*Set->UseTranslationBoneNames[k]);}
  Out->Printf("],\"force_mesh_translation_bones\":[");for(int k=0;k<Set->ForceMeshTranslationBoneNames.Num();k++){if(k)Out->Printf(",");Out->Printf("\"%s\"",*Set->ForceMeshTranslationBoneNames[k]);}
  Out->Printf("]}\n");delete Out;
  FArchive *Bin=CreateExportArchive(Obj,0,"%s/%s.compressed.bin",Obj->Name,*Seq->SequenceName);if(Bin){if(Seq->CompressedByteStream.Num())Bin->Serialize(Seq->CompressedByteStream.GetData(),Seq->CompressedByteStream.Num());delete Bin;}
  appPrintf("HAT_SCALE_AUDIT %s %d %d %d %d\n",*Seq->SequenceName,(int)Seq->ScaleCompressionFormat,Seq->CompressedScaleOffsets.Num(),active,nonunit);
 }
#endif
}

'''
assert s.count(marker)==1
s=s.replace(marker,fn+marker,1).replace('guard(ExportMd5Anim);','guard(ExportMd5Anim);\n\tExportHatSourceMotion(Anim);',1);f.write_text(s,newline='\n');print('PATCHED')
